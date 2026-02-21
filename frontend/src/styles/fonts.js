import {
  Koh_Santepheap,
  Quando,
  Old_Standard_TT,
  Merriweather,
} from "next/font/google";

export const kohSantepheap = Koh_Santepheap({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-koh-santepheap", // Matches your CSS var()
});

export const quando = Quando({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-quando",
});

export const oldStandardTT = Old_Standard_TT({
  subsets: ["latin"],
  weight: ["400", "700"], // We load 700 because your .input class needs it
  variable: "--font-old-standard-tt",
});

export const merriweather = Merriweather({
  subsets: ["latin"],
  weight: ["400", "700", "900"],
  variable: "--font-merriweather",
});
