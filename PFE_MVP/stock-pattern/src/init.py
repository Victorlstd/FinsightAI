import concurrent.futures
import importlib
import json
import logging
import sys
from argparse import ArgumentParser
from datetime import datetime
from importlib.metadata import metadata
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

import utils
from loaders.AbstractLoader import AbstractLoader
from Plotter import Plotter

try:
    from tqdm import tqdm
except ModuleNotFoundError:
    exit("tqdm is required. Run `pip install tqdm` to install")

if metadata("fast_csv_loader")["version"] != "2.0.0":
    exit("fast_csv_loader v2.0.0 is required. Run `pip install -U fast_csv_loader`")


def uncaught_exception_handler(*args):
    """
    Handle all Uncaught Exceptions

    Function passed to sys.excepthook
    """
    logger.critical("Uncaught Exception", exc_info=args)
    cleanup(loader, futures)


def get_loader_class(config):
    # Load data loader from config. Default loader is EODFileLoader
    loader_name = config.get("LOADER", "EODFileLoader")
    loader_module = importlib.import_module(f"loaders.{loader_name}")
    return getattr(loader_module, loader_name)


def cleanup(loader: AbstractLoader, futures: List[concurrent.futures.Future]):
    if futures:
        for future in futures:
            future.cancel()
        concurrent.futures.wait(futures)

    # close loader if needed
    try:
        if not loader.closed:
            loader.close()
    except Exception:
        # be tolerant to loader implementations
        try:
            loader.close()
        except Exception:
            pass


def _dt_to_iso(dt):
    if dt is None:
        return None
    if hasattr(dt, "isoformat"):
        return dt.isoformat()
    return str(dt)


def export_candles_json(
    sym: str, df, timeframe: str, out_path: Path
) -> Optional[Path]:
    if df is None or df.empty:
        return None

    if df.index.has_duplicates:
        df = df.loc[~df.index.duplicated()]

    if not df.index.is_monotonic_increasing:
        df = df.sort_index(ascending=True)

    payload = {
        "sym": sym.upper(),
        "timeframe": timeframe,
        "df_range": {
            "start": _dt_to_iso(df.index[0]),
            "end": _dt_to_iso(df.index[-1]),
            "rows": int(len(df)),
        },
        "candles": [
            {
                "t": _dt_to_iso(ts),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": float(row["Volume"]) if "Volume" in row else None,
            }
            for ts, row in df.iterrows()
        ],
        "meta": {
            "saved_at": datetime.now().isoformat(),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def scan_pattern(
    sym: str,
    pattern: str,
    fns: Tuple[Callable, ...],
    loader: AbstractLoader,
    logger: logging.Logger,
    config: dict,
    bars_left=6,
    bars_right=6,
):
    patterns: List[dict] = []

    df = loader.get(sym)

    if df is None or df.empty:
        return patterns

    if df.index.has_duplicates:
        df = df.loc[~df.index.duplicated()]

    if not df.index.is_monotonic_increasing:
        df = df.sort_index(ascending=True)

    if pattern == "uptl" or pattern == "flagu":
        pivot_type = "low"
    elif pattern == "dntl" or pattern == "flagd":
        pivot_type = "high"
    else:
        pivot_type = "both"

    pivots = utils.get_max_min(
        df, barsLeft=bars_left, barsRight=bars_right, pivot_type=pivot_type
    )

    if not len(pivots):
        return patterns

    for fn in fns:
        if not callable(fn):
            raise TypeError(f"Expected callable. Got {type(fn)}")

        try:
            result = fn(sym, df, pivots, config)
        except Exception as e:
            logger.exception(f"SYMBOL name: {sym}", exc_info=e)
            return patterns

        if result:
            patterns.append(utils.make_serializable(result))

    return patterns


def process(
    sym_list: Tuple[str, ...],
    pattern: str,
    fns: Tuple[Callable, ...],
    futures: List[concurrent.futures.Future],
) -> List[dict]:
    """
    Process ONE detector key (pattern) with its function tuple (fns).
    Returns a list of detected patterns + a meta dict as last item (same behavior as before).
    """
    patterns: List[dict] = []

    # Load or initialize state dict for storing previously detected patterns
    state = None
    state_file = None
    filtered = None

    if config.get("SAVE_STATE", False) and args.file and not args.date:
        state_file = DIR / f"state/{args.file.stem}_{pattern}.json"

        if not state_file.parent.is_dir():
            state_file.parent.mkdir(parents=True)

        if state_file.exists():
            state = json.loads(state_file.read_bytes())
        else:
            state = {}

    # determine the folder to save to in case save option is set
    save_folder: Optional[Path] = None
    image_folder = f"{datetime.now():%d_%b_%y_%H%M}"

    # Disable any image plotting/saving if --no-plot
    if not args.no_plot:
        if "SAVE_FOLDER" in config:
            save_folder = Path(config["SAVE_FOLDER"]) / image_folder

        if args.save:
            save_folder = args.save / image_folder

        if save_folder and not save_folder.exists():
            save_folder.mkdir(parents=True)

    # begin scan process
    with concurrent.futures.ProcessPoolExecutor() as executor:
        for sym in sym_list:
            future = executor.submit(
                scan_pattern,
                sym,
                pattern,
                fns,
                loader,
                logger,
                config,
                bars_left=args.left,
                bars_right=args.right,
            )
            futures.append(future)

        for future in tqdm(
            concurrent.futures.as_completed(futures),
            total=len(futures),
        ):
            try:
                result = future.result()
            except Exception as e:
                cleanup(loader, futures)
                logger.exception("Error in Future - scanning patterns", exc_info=e)
                return []

            patterns.extend(result)

        futures.clear()

        if state is not None:
            filtered = []
            len_state = len(state)
            detected = set()

            for dct in patterns:
                key = f"{dct['sym']}-{dct['pattern']}"
                detected.add(key)

                if not len_state:
                    state[key] = dct
                    filtered.append(dct)
                    continue

                if key in state:
                    if dct.get("start") == state[key].get("start"):
                        continue
                    state[key] = dct
                    filtered.append(dct)
                else:
                    filtered.append(dct)
                    state[key] = dct

            invalid_patterns = set(state.keys()) - detected
            for key in invalid_patterns:
                state.pop(key)

            if state_file:
                state_file.write_text(json.dumps(state, indent=2))
                logger.info(
                    f"\nTo view all current market patterns, run `py init.py --plot state/{state_file.name}`\n"
                )

        patterns_to_output = patterns if state is None else filtered

        if not patterns_to_output:
            return []

        # Save the images if required and not disabled
        if save_folder:
            plotter = Plotter(
                patterns_to_output,
                loader,
                save_folder=save_folder,
                config=config.get("CHART", {}),
            )

            for i in range(len(patterns_to_output)):
                future = executor.submit(plotter.plot, i)
                futures.append(future)

            logger.info("Saving images")

            for future in tqdm(
                concurrent.futures.as_completed(futures), total=len(futures)
            ):
                try:
                    future.result()
                except Exception as e:
                    cleanup(loader, futures)
                    logger.exception("Error in Futures - Saving images", exc_info=e)
                    return []
            futures.clear()

    patterns_to_output.append(
        {
            "timeframe": loader.tf,
            "end_date": args.date.isoformat() if args.date else None,
            "config": str(CONFIG_PATH),
        }
    )

    return patterns_to_output


def resolve_fns_from_key(
    key: str, fn_dict: Dict[str, Callable], config: dict
) -> Tuple[Callable, ...]:
    """
    Supports:
    - custom pattern groups from config["PATTERNS"][key]
    - single detector key in fn_dict
    - legacy groups: bull, bear, bull_harm, bear_harm, all
    """
    if "PATTERNS" in config and key in config["PATTERNS"]:
        custom_list = config["PATTERNS"][key]
        fns: List[Callable] = []
        for k in custom_list:
            if k not in fn_dict:
                raise KeyError(f"No such pattern defined: {k}")
            fns.append(fn_dict[k])
        return tuple(fns)

    if key in fn_dict:
        return (fn_dict[key],)

    if key == "bull":
        bull_list = ("vcpu", "hnsu", "dbot", "flagu")
        return tuple(v for k, v in fn_dict.items() if k in bull_list)

    if key == "bear":
        bear_list = ("vcpd", "hnsd", "dtop", "flagd")
        return tuple(v for k, v in fn_dict.items() if k in bear_list)

    if key == "bull_harm":
        bull_list = ("abcdu", "batu", "gartu", "crabu", "bflyu")
        return tuple(v for k, v in fn_dict.items() if k in bull_list)

    if key == "bear_harm":
        bear_list = ("abcdd", "batd", "gartd", "crabd", "bflyd")
        return tuple(v for k, v in fn_dict.items() if k in bear_list)

    if key == "all":
        return tuple(
            fn_dict[k]
            for k in ("vcpu", "hnsu", "dbot", "flagu", "vcpd", "hnsd", "dtop", "flagd")
        )

    raise KeyError(f"{key} did not match any defined patterns.")


def process_many(
    sym_list: Tuple[str, ...],
    pattern_keys: Tuple[str, ...],
    fn_dict: Dict[str, Callable],
    futures: List[concurrent.futures.Future],
) -> List[dict]:
    """
    Scan MANY detector keys and return ONE merged list with ONE meta at the end.
    (No interactive prompts, no plots.)
    """
    merged: List[dict] = []
    meta: Optional[dict] = None

    for key in pattern_keys:
        fns = resolve_fns_from_key(key, fn_dict, config)

        out = process(sym_list, key, fns, futures)
        if not out:
            continue

        # last item is meta
        meta = out[-1]
        merged.extend(out[:-1])

    if meta is None:
        return []

    merged.append(meta)
    return merged


def print_summary(patterns_with_meta: List[dict]):
    """
    Print only the list of detectors found + counts (no plots).
    """
    if not patterns_with_meta:
        print("No patterns detected")
        return

    data = patterns_with_meta[:-1]  # exclude meta
    if not data:
        print("No patterns detected")
        return

    counts: Dict[str, int] = {}
    for p in data:
        k = p.get("pattern", "unknown")
        counts[k] = counts.get(k, 0) + 1

    detectors = sorted(counts.keys())

    print("\nDetected detectors:")
    for d in detectors:
        print(f"- {d}: {counts[d]}")

    print("\nTip: you can retrace patterns using their `points` field from the json output.\n")


# START
if __name__ == "__main__":
    version = "4.1.0"

    futures: List[concurrent.futures.Future] = []

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
    )

    logger = logging.getLogger(__name__)
    sys.excepthook = uncaught_exception_handler

    # Load configuration
    DIR = Path(__file__).parent

    fn_dict: Dict[str, Callable] = {
        "flagu": utils.find_bullish_flag,
        "flagd": utils.find_bearish_flag,
        "vcpu": utils.find_bullish_vcp,
        "dbot": utils.find_double_bottom,
        "hnsu": utils.find_reverse_hns,
        "vcpd": utils.find_bearish_vcp,
        "dtop": utils.find_double_top,
        "hnsd": utils.find_hns,
        "trng": utils.find_triangles,
        "uptl": utils.find_uptrend_line,
        "dntl": utils.find_downtrend_line,
        "abcdu": utils.find_bullish_abcd,
        "abcdd": utils.find_bearish_abcd,
        "batu": utils.find_bullish_bat,
        "batd": utils.find_bearish_bat,
        "gartu": utils.find_bullish_gartley,
        "gartd": utils.find_bearish_gartley,
        "crabu": utils.find_bullish_crab,
        "crabd": utils.find_bearish_crab,
        "bflyu": utils.find_bullish_butterfly,
        "bflyd": utils.find_bearish_butterfly,
    }

    # Parse CLI arguments
    parser = ArgumentParser(
        description="Python CLI tool to identify common Chart patterns. Includes Harmonic chart patterns.",
        epilog="https://github.com/BennyThadikaran/stock-pattern",
    )

    parser.add_argument(
        "-c",
        "--config",
        type=lambda x: Path(x).expanduser().resolve(),
        default=None,
        metavar="filepath",
        help="Custom config file",
    )

    parser.add_argument(
        "-d",
        "--date",
        type=datetime.fromisoformat,
        metavar="str",
        help="ISO format date YYYY-MM-DD.",
    )

    parser.add_argument(
        "--tf",
        action="store",
        help="Timeframe string.",
    )

    parser.add_argument(
        "-p",
        "--pattern",
        type=str,
        metavar="str",
        help=f"String pattern. One of {', '.join(fn_dict.keys())} or bull, bear, bull_harm, bear_harm, all.",
    )

    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan all detectors (all keys in fn_dict). If --pattern is omitted, this becomes the default behavior.",
    )

    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Disable any plotting/saving images and POST_SCAN_PLOT.",
    )

    parser.add_argument(
        "--output",
        type=lambda x: Path(x).expanduser().resolve(),
        default=None,
        help="Output json file path. If omitted, uses <pattern>-<tf>.json",
    )

    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print only a list of detectors found + counts (no plots).",
    )

    parser.add_argument(
        "-l",
        "--left",
        type=int,
        metavar="int",
        default=6,
        help="Number of candles on left side of pivot",
    )

    parser.add_argument(
        "-r",
        "--right",
        type=int,
        metavar="int",
        default=6,
        help="Number of candles on right side of pivot",
    )

    parser.add_argument(
        "--save",
        type=Path,
        nargs="?",
        const=DIR / "images",
        help="Specify the save directory (disabled when --no-plot is set).",
    )

    parser.add_argument(
        "--idx",
        type=int,
        default=0,
        help="Index to plot",
    )

    # Plot-mode helpers (choose what to display AFTER scan)
    parser.add_argument(
        "--list",
        action="store_true",
        help="When used with --plot: list entries with their indices (no plot).",
    )

    parser.add_argument(
        "--filter-pattern",
        type=str,
        default=None,
        help="When used with --plot: filter items by detector key (e.g. hnsd).",
    )

    parser.add_argument(
        "--filter-sym",
        type=str,
        default=None,
        help="When used with --plot: filter items by symbol (e.g. AAPL).",
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument(
        "-f",
        "--file",
        type=lambda x: Path(x).expanduser().resolve(),
        default=None,
        metavar="filepath",
        help="File containing list of stocks. One on each line",
    )

    group.add_argument(
        "--sym",
        nargs="+",
        metavar="SYM",
        help="Space separated list of stock symbols.",
    )

    group.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Print the current version.",
    )

    group.add_argument(
        "--plot",
        type=lambda x: Path(x).expanduser().resolve(),
        default=None,
        help="Plot results from json file",
    )

    if "-c" in sys.argv or "--config" in sys.argv:
        idx = sys.argv.index("-c" if "-c" in sys.argv else "--config")
        CONFIG_PATH = Path(sys.argv[idx + 1]).expanduser().resolve()
    else:
        CONFIG_PATH = DIR / "user.json"

    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_bytes())
        data_path = Path(config["DATA_PATH"]).expanduser()
    else:
        print(
            "Configuration file is missing. Run `setup-config.py` to setup a `user.json` file"
        )
        exit()

    if config["DATA_PATH"] == "" or not data_path.exists():
        exit("`DATA_PATH` not found or not provided. Edit user.json.")

    sym_list = config["SYM_LIST"] if "SYM_LIST" in config else None

    has_required_arg_set = (
        "-f" in sys.argv
        or "--file" in sys.argv
        or "--sym" in sys.argv
        or "-v" in sys.argv
        or "--version" in sys.argv
        or "--plot" in sys.argv
    )

    if not has_required_arg_set:
        sys.argv.extend(("-f", sym_list if sym_list else config["DATA_PATH"]))

    args = parser.parse_args()

    # Print version
    if args.version:
        exit(
            f"""
Stock-Pattern | Version {version}
Copyright (C) 2023 Benny Thadikaran

Github: https://github.com/BennyThadikaran/stock-pattern

This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it
under certain conditions.
See license: https://www.gnu.org/licenses/gpl-3.0.en.html#license-text
"""
        )

    # PLOT MODE
    if args.plot:
        data = json.loads(args.plot.read_bytes())

        # Last item contains meta data about the timeframe used, end_date etc
        meta = data.pop()

        config = json.loads(Path(meta["config"]).expanduser().resolve().read_bytes())
        loader_class = get_loader_class(config)

        end_date = None
        if meta.get("end_date"):
            end_date = datetime.fromisoformat(meta["end_date"])

        try:
            loader = loader_class(
                config,
                meta["timeframe"],
                end_date=end_date,
            )
        except ValueError as e:
            logger.exception("", exc_info=e)
            exit()

        # Apply filters for listing/plotting
        filtered = data
        if args.filter_pattern:
            fp = args.filter_pattern.lower().strip()
            filtered = [p for p in filtered if str(p.get("pattern", "")).lower() == fp]
        if args.filter_sym:
            fs = args.filter_sym.upper().strip()
            filtered = [p for p in filtered if str(p.get("sym", "")).upper() == fs]

        if args.list:
            if not filtered:
                print("No entries match filters.")
                cleanup(loader, futures)
                exit()

            for i, p in enumerate(filtered):
                sym = p.get("sym", "")
                pat = p.get("pattern", "")
                start = p.get("start", "")
                end = p.get("end", "")
                print(f"[{i}] {sym} | {pat} | {start} -> {end}")

            cleanup(loader, futures)
            exit()

        if not filtered:
            print("No entries match filters.")
            cleanup(loader, futures)
            exit()

        plotter = Plotter(filtered, loader, config=config.get("CHART", {}))
        plotter.plot(args.idx)
        cleanup(loader, futures)
        exit()

    # SCAN MODE
    loader_class = get_loader_class(config)

    try:
        loader = loader_class(
            config,
            args.tf,
            end_date=args.date,
        )
    except ValueError as e:
        logger.exception("", exc_info=e)
        exit()

    # If user didn't specify a pattern, default to scan all (no more interactive selection)
    if not args.pattern and not args.scan_all:
        args.scan_all = True

    # Load symbol list
    if args.file:
        if args.file.is_dir():
            data = tuple(file.name[:-4] for file in args.file.iterdir())
        else:
            data = tuple(args.file.read_text().strip().split("\n"))
    else:
        data = tuple(args.sym)

    # Always export candle jsons per symbol, even if no patterns are found.
    if "SAVE_FOLDER" in config and config["SAVE_FOLDER"]:
        candle_out_dir = Path(config["SAVE_FOLDER"]).expanduser().resolve() / "candles"
    else:
        candle_out_dir = DIR / "candles"

    for sym in data:
        df = loader.get(sym)
        if df is None or df.empty:
            continue
        export_candles_json(
            sym,
            df,
            loader.tf,
            candle_out_dir / f"{sym.upper()}_{loader.tf}.json",
        )

    try:
        if args.scan_all:
            pattern_keys = tuple(fn_dict.keys())
            logger.info(
                f"Scanning ALL detectors ({len(pattern_keys)}) on `{loader.tf}`. Press Ctrl - C to exit"
            )
            patterns = process_many(data, pattern_keys, fn_dict, futures)
            key_for_filename = "scan_all"
        else:
            key = args.pattern.strip().lower()
            fns = resolve_fns_from_key(key, fn_dict, config)

            logger.info(
                f"Scanning `{key.upper()}` patterns on `{loader.tf}`. Press Ctrl - C to exit"
            )

            patterns = process(data, key, fns, futures)
            key_for_filename = key

    except KeyboardInterrupt:
        cleanup(loader, futures)
        logger.info("User exit")
        exit()

    count = len(patterns)

    # Determine output directory for per-symbol pattern jsons
    if args.output:
        output_dir = args.output if args.output.is_dir() else args.output.parent
    elif "SAVE_FOLDER" in config and config["SAVE_FOLDER"]:
        output_dir = Path(config["SAVE_FOLDER"]).expanduser().resolve() / "patterns"
    else:
        output_dir = DIR / "patterns"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Split meta from patterns if present
    meta = None
    data_patterns = patterns
    if patterns and isinstance(patterns[-1], dict):
        last = patterns[-1]
        if "timeframe" in last and "config" in last:
            meta = last
            data_patterns = patterns[:-1]

    if meta is None:
        meta = {
            "timeframe": loader.tf,
            "end_date": args.date.isoformat() if args.date else None,
            "config": str(CONFIG_PATH),
        }

    # Group patterns by symbol and write one json per symbol
    patterns_by_sym: Dict[str, List[dict]] = {}
    for p in data_patterns:
        sym = str(p.get("sym", "")).upper()
        if not sym:
            continue
        patterns_by_sym.setdefault(sym, []).append(p)

    for sym in data:
        sym_upper = str(sym).upper()
        sym_patterns = patterns_by_sym.get(sym_upper, [])
        payload = {
            "sym": sym_upper,
            "timeframe": meta.get("timeframe"),
            "patterns": sym_patterns,
            "meta": meta,
        }
        if not sym_patterns:
            payload["message"] = "no patterns detected"
        out_path = output_dir / f"{sym_upper}_{loader.tf}_patterns.json"
        out_path.write_text(json.dumps(payload, indent=2))

    # Summary / next step
    if args.summary:
        print_summary(patterns)

    logger.info(
        f"Got {max(count - 1, 0)} patterns.\nOutput dir: {output_dir}\n\nUse `py init.py --plot <file>` then `--list` to choose which one to display."
    )

    # Disable any automatic plot after scan (especially for scan_all)
    do_post_scan_plot = (
        config.get("POST_SCAN_PLOT", True)
        and not args.save
        and not args.no_plot
        and not args.scan_all
    )

    if do_post_scan_plot:
        # last item is meta
        patterns_no_meta = patterns[:-1]
        plotter = Plotter(patterns_no_meta, loader, config=config.get("CHART", {}))
        plotter.plot()

    cleanup(loader, futures)
