"use client";

import {
  useState,
  useEffect,
  useActionState,
  useRef,
  useCallback,
} from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import Form from "next/form";
import { updatePropertyAction } from "@/actions/propertyActions";
import UpdateAlert from "@/components/alerts/UpdateAlert";
import { FormButton } from "@/components/buttons/Buttons";
import styles from "./CreateListingForm.module.css";

const uploadIcon = "/assets/upload-icon.svg";
const doneIcon = "/assets/done.svg";
const notDoneIcon = "/assets/not-done.svg";

function parseAddressFunc(addressString) {
  const address = {};
  const pairs = addressString.split(", ");

  pairs.forEach((pair) => {
    const [key, value] = pair.split("=");
    address[key] = value;
  });

  return address;
}

export default function UpdateListingClient({ propertyId, initialData }) {
  const [state, formAction, isPending] = useActionState(
    updatePropertyAction.bind(null, propertyId),
    {
      errors: {},
      success: "",
      formPropertyData: initialData,
      initialPropertyData: initialData,
    },
  );

  const parsedAddress = parseAddressFunc(state.initialPropertyData?.address);
  const [formData, setFormData] = useState({
    title: state.initialPropertyData?.title || "",
    description: state.initialPropertyData?.description || "",
    country: parsedAddress?.country || "",
    state: parsedAddress?.state || "",
    city: parsedAddress?.city || "",
    area: parsedAddress?.area || "",
    street: parsedAddress?.street || "",
    house_no: parsedAddress?.house_no || "",
    flat_no: parsedAddress?.flat_no || "",
    beds: state.initialPropertyData?.beds || "",
    baths: state.initialPropertyData?.baths || "",
    area_sqft: state.initialPropertyData?.area_sqft || "",
    price: state.initialPropertyData?.price || "",
  });

  const [previewUrl, setPreviewUrl] = useState(
    state.formPropertyData?.image_url || null,
  );
  const [localImageError, setLocalImageError] = useState("");
  const [displaySuccess, setDisplaySuccess] = useState("");
  const fileInputRef = useRef(null);
  const textAreaRef = useRef(null);
  const router = useRouter();

  const addressChanged =
    formData.country !== parsedAddress?.country ||
    formData.state !== parsedAddress?.state ||
    formData.city !== parsedAddress?.city ||
    formData.area !== parsedAddress?.area ||
    formData.street !== parsedAddress?.street ||
    formData.house_no !== parsedAddress?.house_no ||
    formData.flat_no !== (parsedAddress?.flat_no || "");

  const detailsChanged =
    String(formData.beds) !== String(state.initialPropertyData?.beds || "") ||
    String(formData.baths) !== String(state.initialPropertyData?.baths || "") ||
    String(formData.area_sqft) !==
      String(state.initialPropertyData?.area_sqft || "");

  const hasUnsavedChanges =
    formData.title !== state.initialPropertyData?.title ||
    formData.description !== state.initialPropertyData?.description ||
    addressChanged ||
    detailsChanged ||
    String(formData.price) !== String(state.initialPropertyData?.price || "") ||
    previewUrl !== state.formPropertyData?.image_url;

  const isTitleComplete =
    formData.title.trim() !== "" &&
    formData.title !== state.initialPropertyData?.title;

  const isDescriptionComplete =
    formData.description.trim() !== "" &&
    formData.description !== state.initialPropertyData?.description;

  const isAddressComplete =
    formData.country.trim() !== "" &&
    formData.house_no.trim() !== "" &&
    addressChanged;

  const isDetailsComplete =
    formData.beds !== "" && formData.baths !== "" && detailsChanged;

  const isPricingComplete =
    formData.price !== "" &&
    String(formData.price) !== String(state.initialPropertyData?.price || "");

  const isImageComplete =
    previewUrl !== null && previewUrl !== state.formPropertyData?.image_url;

  const resetImageInput = useCallback(() => {
    setPreviewUrl(state.formPropertyData.image_url);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [state.formPropertyData.image_url]);

  const handleInputChange = (e) => {
    const { type, name, value } = e.target;
    let newValue = value;

    if (type === "number") {
      if (value === "") {
        newValue = "";
      } else {
        const limits = {
          price: /^\d{0,13}(\.\d{0,2})?$/,
          area_sqft: /^\d{0,10}$/,
          beds: /^\d{0,5}$/,
          baths: /^\d{0,5}$/,
        };

        if (limits[name] && !limits[name].test(value)) {
          return;
        }

        newValue = value;
      }
    }
    setFormData((prev) => ({ ...prev, [name]: newValue }));
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setLocalImageError("");
      const validTypes = ["image/jpeg", "image/png", "image/jpg"];
      const isInvalidType = !validTypes.includes(file.type);
      const isTooLarge = file.size > 2 * 1024 * 1024;

      if (isInvalidType || isTooLarge) {
        const msg = isInvalidType
          ? "Only JPG, JPEG and PNG images are allowed."
          : "Image size should not exceed 2MB.";

        setLocalImageError(msg);
        resetImageInput();
        return;
      }

      if (previewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(previewUrl);
      }

      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleIconClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const autoResize = (element) => {
    if (element) {
      element.style.height = "auto";
      element.style.height = element.scrollHeight + "px";
    }
  };

  useEffect(() => {
    if (isPending) {
      setLocalImageError("");
    }
  }, [isPending]);

  useEffect(() => {
    autoResize(textAreaRef.current);
  }, [formData.description]);

  useEffect(() => {
    const handleResize = () => autoResize(textAreaRef.current);
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  useEffect(() => {
    if (state.errors && state.errors.image_url) {
      resetImageInput();
    }
  }, [state.errors, resetImageInput]);

  useEffect(() => {
    if (state.success) {
      setDisplaySuccess(state.success);

      const parsedAddress = parseAddressFunc(
        state.initialPropertyData?.address,
      );
      setFormData(() => ({
        ...state.initialPropertyData,
        ...parsedAddress,
      }));
      setLocalImageError("");
      resetImageInput();

      const timer = setTimeout(() => {
        setDisplaySuccess("");
        router.refresh();
      }, 3000);

      return () => clearTimeout(timer);
    }
  }, [state.success, state.initialPropertyData, router, resetImageInput]);

  return (
    <div className={styles.container}>
      <UpdateAlert hasUnsavedChanges={hasUnsavedChanges} />
      <div className={styles.sidebar}>
        <div className={styles.sidebarContent}>
          <div className={styles.sidebarHeader}>
            <div className={styles.sidebarTitle}>Update a listing</div>
            <div className={styles.sidebarSubtitle}>
              Input property information
            </div>
          </div>

          <div className={styles.checklist}>
            {[
              { label: "Title", check: isTitleComplete },
              { label: "Description", check: isDescriptionComplete },
              { label: "Address", check: isAddressComplete },
              { label: "Details", check: isDetailsComplete },
              { label: "Pricing", check: isPricingComplete },
              { label: "Image", check: isImageComplete },
            ].map((item, idx) => (
              <div key={idx} className={styles.checkItem}>
                <div>
                  <Image
                    src={item.check ? doneIcon : notDoneIcon}
                    alt="status"
                    width={24}
                    height={24}
                    className={styles.icon}
                  />
                </div>
                <div className={styles.label}>{item.label}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className={styles.formContainer}>
        <Form action={formAction}>
          <div className={styles.section}>
            <div className={styles.sectionTitle}>Title</div>
            <input
              type="text"
              name="title"
              value={formData.title}
              placeholder="Title"
              onChange={handleInputChange}
              className={styles.input}
            />
            {Object.keys(state.errors).length > 0 && state.errors.title && (
              <div className={styles.errorBox}>{state.errors.title}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Description</div>
            <div className={styles.descContainer}>
              <textarea
                name="description"
                ref={textAreaRef}
                placeholder="Description"
                value={formData.description}
                onChange={handleInputChange}
                className={styles.storedText}
                maxLength={150}
              />
              <div className={styles.charCount}>
                {formData.description.length} / 150
              </div>
            </div>
            {Object.keys(state.errors).length > 0 &&
              state.errors.description && (
                <div className={styles.errorBox}>
                  {state.errors.description}
                </div>
              )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Address</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Country*</h1>
                <input
                  type="text"
                  placeholder="Country"
                  name="country"
                  value={formData.country}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>State*</h1>
                <input
                  type="text"
                  placeholder="State"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>City*</h1>
                <input
                  type="text"
                  placeholder="City"
                  name="city"
                  value={formData.city}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Area*</h1>
                <input
                  type="text"
                  placeholder="Area"
                  name="area"
                  value={formData.area}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Street*</h1>
                <input
                  type="text"
                  placeholder="Street"
                  name="street"
                  value={formData.street}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>House No.*</h1>
                <input
                  type="text"
                  placeholder="House No."
                  name="house_no"
                  value={formData.house_no}
                  onChange={handleInputChange}
                  className={styles.input}
                />
              </div>
            </div>

            <div className={styles.inputContainer}>
              <h1 className={styles.inputTitle}>Flat No. (optional)</h1>
              <input
                type="text"
                placeholder="Flat No."
                name="flat_no"
                value={formData.flat_no}
                onChange={handleInputChange}
                className={styles.input}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.address && (
              <div className={styles.errorBox}>{state.errors.address}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Details</div>
            <div className={styles.gridThree}>
              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Beds*</h1>
                <input
                  type="number"
                  placeholder="Beds"
                  name="beds"
                  value={formData.beds}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 && state.errors.beds && (
                  <div className={styles.errorBox}>{state.errors.beds}</div>
                )}
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Baths*</h1>
                <input
                  type="number"
                  placeholder="Baths"
                  name="baths"
                  value={formData.baths}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 && state.errors.baths && (
                  <div className={styles.errorBox}>{state.errors.baths}</div>
                )}
              </div>

              <div className={styles.inputContainer}>
                <h1 className={styles.inputTitle}>Sqft*</h1>
                <input
                  type="number"
                  placeholder="Sqft"
                  name="area_sqft"
                  value={formData.area_sqft}
                  onChange={handleInputChange}
                  className={styles.input}
                />
                {Object.keys(state.errors).length > 0 &&
                  state.errors.area_sqft && (
                    <div className={styles.errorBox}>
                      {state.errors.area_sqft}
                    </div>
                  )}
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Pricing</div>
            <div className={styles.priceInputWrapper}>
              <div className={styles.dollarSign}>$</div>
              <input
                type="number"
                name="price"
                placeholder="0.00"
                value={formData.price}
                onChange={handleInputChange}
                className={styles.priceInput}
              />
            </div>
            {Object.keys(state.errors).length > 0 && state.errors.price && (
              <div className={styles.errorBox}>{state.errors.price}</div>
            )}
          </div>

          <div className={styles.section}>
            <div className={styles.sectionTitle}>Image</div>
            <div
              className={
                previewUrl
                  ? styles.imageUploadBox
                  : styles.singleUploadContainer
              }
            >
              {previewUrl && (
                <div className={styles.imagePreviewContainer}>
                  <Image
                    src={previewUrl}
                    alt="Preview"
                    width={400}
                    height={300}
                    className={styles.imagePreview}
                  />
                </div>
              )}

              <div className={styles.uploadControlSide}>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleImageChange}
                  name="property_image"
                  accept="image/*"
                  className={styles.imageInput}
                  style={{ display: "none" }}
                  disabled={isPending}
                />
                <input
                  type="hidden"
                  name="client_preview_url"
                  value={previewUrl}
                />
                <div className={styles.uploadLabel}>
                  <div
                    className={styles.uploadIconCircle}
                    onClick={handleIconClick}
                  >
                    <Image
                      src={uploadIcon}
                      alt="Upload"
                      width={30}
                      height={30}
                    />
                  </div>
                  <div className={styles.uploadText}>Choose File to Upload</div>
                  <div className={styles.uploadSubtext}>
                    Maximum Upload Size 2MB
                  </div>
                </div>
              </div>
            </div>
            {localImageError ? (
              <span className={styles.errorBox}>{localImageError}</span>
            ) : Object.keys(state.errors).length > 0 &&
              state.errors.image_url ? (
              <span className={styles.errorText}>{state.errors.image_url}</span>
            ) : null}
          </div>

          {displaySuccess && (
            <div className={styles.successBox}>{displaySuccess}</div>
          )}
          {Object.keys(state.errors).length > 0 && state.errors.general && (
            <div className={styles.errorBox2}>{state.errors.general}</div>
          )}

          <div className={styles.buttonGroup}>
            <div className={styles.cancelProfileButton}>
              <Link
                href={`/properties/${state.initialPropertyData.slug}`}
                className={styles.cancelProfileButtonLink}
              >
                Cancel
              </Link>
            </div>
            <FormButton
              type="submit"
              text="Update"
              pendingText="Updating..."
              disabled={isPending}
              className={styles.submitBtn}
            />
          </div>
        </Form>
      </div>
    </div>
  );
}
