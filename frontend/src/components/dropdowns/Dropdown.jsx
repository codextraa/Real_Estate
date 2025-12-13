"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import styles from "./Dropdown.module.css";
import Image from "next/image";

const houseIcon = "/assets/house-icon.svg";
const doorIcon = "/assets/door-icon.svg";
const addressIcon = "/assets/location-icon.svg";
const dollarIcon = "/assets/dollar-icon.svg";
const toiletIcon = "/assets/toilet-icon.svg";

export default function Dropdown() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const [filters, setFilters] = useState({
    address: searchParams.get("address") || "California",
    price_min: searchParams.get("price_min") || "1000",
    price_max: searchParams.get("price_max") || "10000",
    area_sqft_min: searchParams.get("area_sqft_min") || "1000",
    area_sqft_max: searchParams.get("area_sqft_max") || "2000",
    baths: searchParams.get("baths") || "3",
    beds: searchParams.get("beds") || "4",
  });

  useEffect(() => {
    setFilters({
      address: searchParams.get("address") || "California",
      price_min: searchParams.get("price_min") || "1000",
      price_max: searchParams.get("price_max") || "10000",
      area_sqft_min: searchParams.get("area_sqft_min") || "1000",
      area_sqft_max: searchParams.get("area_sqft_max") || "2000",
      baths: searchParams.get("baths") || "3",
      beds: searchParams.get("beds") || "4",
    });
  }, [searchParams]);

  const [dropdownOpen, setDropdownOpen] = useState({
    address: false,
    price: false,
    area_sqft: false,
    baths: false,
    beds: false,
  });

  const filterOptions = {
    address: [
      "California",
      "New York",
      "Texas",
      "Florida",
      "Washington",
      "Oregon",
      "Arizona",
      "Colorado",
      "Nevada",
      "Utah",
    ],
    price: [
      "$1000 - $10000",
      "$10000 - $50000",
      "$50000 - $100000",
      "$100000 - $200000",
      "$200000 - $500000",
      "$500000 - $1000000",
    ],
    area_sqft: [
      "1000 sqft - 2000 sqft",
      "2000 sqft - 5000 sqft",
      "5000 sqft - 10000 sqft",
      "10000 sqft - 20000 sqft",
      "20000 sqft - 50000 sqft",
      "50000 sqft - 100000 sqft",
    ],
    baths: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
    beds: ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
  };

  const parseRangeValue = (rangeString) => {
    const cleanedString = rangeString.replace(/[$,a-z\s]/gi, "");
    const parts = cleanedString.split("-");

    if (parts.length === 2) {
      return {
        min: parts[0].trim(),
        max: parts[1].trim(),
      };
    }
    return { min: "", max: "" };
  };

  const toggleDropdown = (dropdown) => {
    setDropdownOpen((prev) => ({
      address: false,
      price: false,
      area_sqft: false,
      baths: false,
      beds: false,
      [dropdown]: !prev[dropdown],
    }));
  };

  const handleFilterChange = (filterType, value) => {
    let updatedFields = {};

    if (filterType === "price" || filterType === "area_sqft") {
      const { min, max } = parseRangeValue(value);

      updatedFields = {
        [`${filterType}_min`]: min,
        [`${filterType}_max`]: max,
      };
    } else {
      updatedFields = {
        [filterType]: value,
      };
    }

    const newFilters = { ...filters, ...updatedFields };
    setFilters(newFilters);
    setDropdownOpen((prev) => ({ ...prev, [filterType]: false }));

    const params = new URLSearchParams(searchParams.toString());

    params.set("page", "1");

    Object.keys(newFilters).forEach((key) => {
      params.set(key, newFilters[key]);
    });

    router.push(`?${params.toString()}`);
  };

  const getFilterDisplayValue = (filterType) => {
    if (filterType === "price") {
      const min = filters.price_min;
      const max = filters.price_max;
      return `$${min} - $${max}`;
    }
    if (filterType === "area_sqft") {
      const min = filters.area_sqft_min;
      const max = filters.area_sqft_max;
      return `${min} sqft - ${max} sqft`;
    }
    return filters[filterType];
  };

  const filtersConfig = [
    {
      filterType: "address",
      icon: addressIcon,
      label: "Address",
      styleClass: "addressFilter",
    },
    {
      filterType: "price",
      icon: dollarIcon,
      label: "Price",
      styleClass: "priceFilter",
    },
    {
      filterType: "area_sqft",
      icon: houseIcon,
      label: "Area (Sqft)",
      styleClass: "areaSqftFilter",
    },
    {
      filterType: "beds",
      icon: doorIcon,
      label: "Bedrooms",
      styleClass: "bedroomsFilter",
    },
    {
      filterType: "baths",
      icon: toiletIcon,
      label: "Bathrooms",
      styleClass: "bathroomsFilter",
    },
  ];

  return (
    <div className={styles.propertyDropdowns}>
      {filtersConfig.map((config) => (
        <div key={config.filterType} className={styles[config.styleClass]}>
          <button
            onClick={() => toggleDropdown(config.filterType)}
            className={styles[`${config.filterType}Button`]}
          >
            <Image
              src={config.icon}
              alt={`${config.filterType} icon`}
              className={styles[`${config.filterType}Icon`]}
              width={24}
              height={24}
            />
            <div className={styles[`${config.filterType}Texts`]}>
              <div className={styles[`${config.filterType}Label`]}>
                {config.label}
              </div>
              <div className={styles[`${config.filterType}Value`]}>
                {getFilterDisplayValue(config.filterType)}
              </div>
            </div>
          </button>
          {dropdownOpen[config.filterType] && (
            <div className={styles[`${config.filterType}Dropdown`]}>
              {filterOptions[config.filterType].map((option) => (
                <button
                  key={option}
                  onClick={() => handleFilterChange(config.filterType, option)}
                  className={styles[`${config.filterType}DropdownItem`]}
                >
                  {option}
                </button>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
