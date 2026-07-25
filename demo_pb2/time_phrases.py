"""
time_phrases.py — natural-English phrasings for every minute of the clock.

Scales the v7 talking-clock corpus from 36 hand-picked phrases to the full
12 x 60 = 720 time space, each rendered in ONE canonical natural phrasing:

    m == 0            -> "it is {H} o'clock"
    m == 15           -> "it is quarter past {H}"
    m == 30           -> "it is half past {H}"
    m == 45           -> "it is quarter to {H+1}"
    1 <= m <= 29      -> "it is {mins(m)} past {H}"
    31 <= m <= 59     -> "it is {mins(60-m)} to {H+1}"

Hours are 1..12 (H+1 wraps 12 -> 1). Pure stdlib so the phrasing layer is
testable without numpy / the container; the heavy LPC analysis consumes this
list downstream. Keeping exactly one phrasing per (h, m) makes the corpus
size a clean 720 and the demo's scaling story unambiguous. Alternate
phrasings ("three oh five", "noon"/"midnight") are noted below as optional
augmentation, deliberately left out of the base corpus.
"""

ONES = ["", "one", "two", "three", "four", "five", "six", "seven", "eight",
        "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen",
        "sixteen", "seventeen", "eighteen", "nineteen"]
TENS = {20: "twenty"}  # only 20..29 appear in the "past/to" minute words


def minute_words(m):
    """English for a minute count 1..29 (as used after past/to)."""
    if not 1 <= m <= 29:
        raise ValueError(f"minute_words expects 1..29, got {m}")
    if m < 20:
        return ONES[m]
    if m == 20:
        return "twenty"
    return f"twenty-{ONES[m - 20]}"


def hour_name(h):
    """Clock hour 1..12."""
    return ONES[h]  # ONES[1..12] cover one..twelve


def wrap_hour(h):
    """Next hour on a 12-hour face: 12 -> 1."""
    return h % 12 + 1


def time_phrase(h, m):
    """Canonical natural phrasing for hour h in 1..12, minute m in 0..59."""
    if not 1 <= h <= 12:
        raise ValueError(f"hour must be 1..12, got {h}")
    if not 0 <= m <= 59:
        raise ValueError(f"minute must be 0..59, got {m}")
    if m == 0:
        body = f"{hour_name(h)} o'clock"
    elif m == 15:
        body = f"quarter past {hour_name(h)}"
    elif m == 30:
        body = f"half past {hour_name(h)}"
    elif m == 45:
        body = f"quarter to {hour_name(wrap_hour(h))}"
    elif m < 30:
        body = f"{minute_words(m)} past {hour_name(h)}"
    else:  # 31..59, not 45
        body = f"{minute_words(60 - m)} to {hour_name(wrap_hour(h))}"
    return f"it is {body}"


def all_times():
    """Yield (h, m, text) for every one of the 720 clock minutes."""
    for h in range(1, 13):
        for m in range(0, 60):
            yield h, m, time_phrase(h, m)


if __name__ == "__main__":
    rows = list(all_times())
    print(f"total utterances: {len(rows)}")
    # unique vocabulary (words across the whole corpus)
    vocab = sorted({w for _, _, t in rows for w in t.split()})
    print(f"vocabulary size: {len(vocab)} words")
    print("vocab:", " ".join(vocab))
    print("\nsamples across the special/general cases:")
    for h, m in [(3, 0), (3, 1), (3, 5), (3, 15), (3, 20), (3, 25),
                 (3, 30), (3, 35), (3, 45), (3, 59), (12, 30), (12, 45)]:
        print(f"  {h:2d}:{m:02d}  ->  {time_phrase(h, m)}")
