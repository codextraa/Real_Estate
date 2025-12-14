"use client";

import { useState } from "react";
import { useRouter, useSearchParams, usePathname } from "next/navigation";
import styles from "./Searchbar.module.css";
import Image from "next/image";

const searchIcon = "/assets/search-icon.svg";

export default function Searchbar() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const initialQuery = searchParams.get("search") || "";
  const [searchTerm, setSearchTerm] = useState(initialQuery);

  const handleSearch = (e) => {
    e.preventDefault();

    const params = new URLSearchParams(searchParams.toString());

    if (searchTerm.trim()) {
      params.set("search", searchTerm.trim());
    } else {
      params.delete("search");
    }

    if (params.has("page")) {
      params.delete("page");
    }

    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <form className={styles.searchbarForm} onSubmit={handleSearch}>
      <button type="submit" className={styles.searchButton}>
        <Image
          src={searchIcon}
          alt="Search Icon"
          width={20}
          height={20}
          className={styles.searchIcon}
        />
      </button>
      <input
        type="text"
        placeholder="Search for an address, city, zip, or listing ID..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className={styles.searchInput}
      />
    </form>
  );
}
