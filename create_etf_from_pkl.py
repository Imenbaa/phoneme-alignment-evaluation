import pickle
from collections import defaultdict

def pkl_to_etf(pkl_path, output_path, use_hyp=True):

    with open(pkl_path, "rb") as f:
        data = pickle.load(f)

    with open(output_path, "w", encoding="utf-8") as out:

        for filename, content in data.items():

            style = content.get("style", "-")

            key = "hyp_intervals" if use_hyp else "ref_intervals"
            intervals = sorted(content[key], key=lambda x: x["start"])

            if not intervals:
                continue

            #récupérer tous les phonèmes présents
            phonemes = sorted(set(seg["phoneme"] for seg in intervals))

            # timeline complète (tous segments)
            for target_phoneme in phonemes:

                for seg in intervals:
                    start = seg["start"]
                    end = seg["end"]
                    duration = end - start
                    phoneme = seg["phoneme"]

                    if duration <= 0:
                        continue

                    # logique clé
                    decision = "t" if phoneme == target_phoneme else "f"

                    line = (
                        f"{filename} 1 "
                        f"{start:.6f} {duration:.6f} "
                        f"sc - {target_phoneme} - {decision}\n"
                    )

                    out.write(line)
