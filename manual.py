from src.list_builder import ManualListBuilder

arts = {
    "Sword arts": {
        "Kenjutsu (Swordsmanship)": {
            "Chūdan no Kamae (Middle Guard)": "A defensive stance where the sword is held at shoulder height, angled towards the opponent. In Shingetsu-ryū, this form allows for the application of the Lunar Dash to close the distance rapidly, followed by a swift upward slash using the tachi.",
            "Hoshizora Giri (Starry Sky Cut)": "A diagonal, downward cut performed with speed and precision to attack from an unexpected angle. The user steps off the line while executing the cut, making it hard to predict. The power Lunar Step allows for the practitioner to add velocity and unpredictability to this move, making it harder for an opponent to react.",
            "Mawari Giri (Rotating Cut)": "A circular cut that starts from above the practitioner’s head and slices downward, finishing with the sword sweeping across the opponent’s body. This cut is often used when an enemy is too close to perform a traditional vertical strike. When empowered with Moonlight Slash, the user can enhance the cut with moonlight energy, turning it into a wider, more devastating attack capable of striking multiple targets within range.",
            "Kiri-Ochi (Ending Cut)": "A decisive vertical cut aimed at finishing off an opponent after a series of defensive or probing strikes. The practitioner uses this to exploit openings after creating a safe distance.",
        },
        "Kodachijutsu (Short Sword Techniques)": {
            "Kiri Giri (Cutting Cut)": "A quick thrust or slash from the kodachi aimed at exploiting the openings in an opponent’s guard. In Shingetsu-ryū, this cut is often used in tight spaces where the longer tachi would be unwieldy. Lunar Bind can be used to bind the opponent’s weapon or body momentarily, allowing for a quick thrust or cut to a vital point.",
            "Sokui Giri (Intercepting Cut)": "A rapid parry and counterattack that allows the practitioner to intercept an opponent’s attack and immediately retaliate with a thrust or cut. This form is used when the practitioner faces a larger or stronger opponent. When paired with Lunar Dash, the practitioner can close the distance with sudden speed, adding extra force to the counterattack.",
        },
        "Ryōtōjutsu (Dual Sword Techniques)": {
            "Tō-Ryō-Harai (Sword Sweep)": "A defensive maneuver where both swords are used to deflect and control multiple incoming strikes, followed by a sweeping motion that clears the opponent’s guard. By using the power of Moonlit Armaments, the swords can briefly take on the properties of solidified moonlight, increasing the precision and cutting ability of the sweep.",
            "Sōryū-no-Kiri (Twin Dragon Slash)": "A two-part attack where the practitioner first strikes with the tachi from above, followed immediately by a low, sweeping cut from the kodachi. This form aims to confuse and disorient the opponent by constantly changing angles. The form can be enhanced with Lunar Dash to quickly close the gap and execute the twin strikes almost simultaneously.",
        },
    },
    "Sōjutsu (Spear Techniques)": {
        "__options": {"extra_depth": 1},
        "Gekkō Yari (Moonlight Spear)": "A thrusting technique where the practitioner extends the jumonji yari in a precise line, aiming for vital points. The spear tip is aimed at an opponent’s chest, throat, or eyes. When augmented with Crater Impact, the spear can release a burst of lunar energy upon impact, increasing the strike's force and range.",
        "Kage Tsuki (Shadow Thrust)": "A deceptive thrust that begins as a feint to one side, followed by a sudden redirect to the other side to pierce through the opponent’s guard. This form works especially well in low-visibility conditions or against distracted opponents. Celestial Whisper can be used to communicate with allies for support, ensuring the practitioner is not overwhelmed.",
        "Gōin-no-Kiri (Heavy Cutting Strike)": "A heavy, downward cut from above performed with the jumonji yari, aimed at breaking through an opponent’s guard. When empowered with Lunar Bind, the user can momentarily disable the opponent’s weapon or shield, making it easier to land the strike.",
    },
}

builder = ManualListBuilder("List of Combat Arts", arts)
wiki_table = builder.build()
print(wiki_table)
