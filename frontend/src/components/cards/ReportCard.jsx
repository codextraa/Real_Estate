// // src/components/cards/ReportCard.jsx
// "use client";
// import { getReportAction } from "@/actions/reportActions";
// import DeleteModal from "../modals/DeleteModal";
// import { DeleteButton } from "../buttons/Buttons";
// import { useState } from "react";
// import styles from "./ReportCard.module.css";

// export default function ReportCard({ report }) {
//   const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
//   const [isDetailsModalOpen, setIsDetailsModalOpen] = useState(false); // New State
//   const [details, setDetails] = useState(null); // New State
//   const [loading, setLoading] = useState(false);

//   const rating = parseFloat(report.investment_rating);
//   const handleOpenDetails = async () => {
//     setIsModalOpen(true);
//     setLoading(true);
//     const response = await getReportAction(report.id);

//     if (response.data) {
//       setDetails(response.data);
//     } else {
//       console.error(response.error);
//     }
//     setLoading(false);
//   };

//   const openDeleteModal = () => {
//     setIsDeleteModalOpen(true);
//     document.body.style.overflow = "hidden";
//   };

//   const closeDeleteModal = () => {
//     setIsDeleteModalOpen(false);
//     document.body.style.overflow = "auto";
//   };

//   return (
//     <div className={styles.card}>
//       <div className={styles.header}>
//         <h3>Report #{report.id}</h3>
//         <span
//           className={`${styles.statusBadge} ${styles[report.status.toLowerCase()]}`}
//         >
//           {report.status}
//         </span>
//       </div>

//       <div className={styles.body}>
//         <div className={styles.infoRow}>
//           <span>Average Price:</span>{" "}
//           <strong>${report.avg_market_price}</strong>
//         </div>
//         <div className={styles.infoRow}>
//           <span>Price Per Sqft:</span>{" "}
//           <strong>${report.avg_price_per_sqft}</strong>
//         </div>
//         <div className={styles.infoRow}>
//           <span>Area:</span>{" "}
//           <strong>
//             {report.extracted_area}, {report.extracted_city}
//           </strong>
//         </div>

//         <div className={styles.ratingSection}>
//           <span>Investment Rating: {rating}/5.0</span>
//           <div className={styles.stars}>
//             {[...Array(5)].map((_, i) => (
//               <span
//                 key={i}
//                 className={
//                   i < Math.floor(rating) ? styles.starFilled : styles.starEmpty
//                 }
//               >
//                 ★
//               </span>
//             ))}
//           </div>
//         </div>
//       </div>

//       <div className={styles.actions}>
//         <button className={styles.detailsBtn} onClick={handleOpenDetails}>
//           Details
//         </button>
//         <div className={styles.deleteProfileButton}>
//           <DeleteButton
//             text="Delete"
//             type="button"
//             onClick={openDeleteModal}
//             className={styles.deleteButton}
//           />
//         </div>
//       </div>
//       {isDeleteModalOpen && (
//         <DeleteModal
//           title="Are you sure you want to delete your report?"
//           userData={report}
//           userRole="Agent"
//           actionName="deleteReport"
//           onCancel={closeDeleteModal}
//         />
//       )}
//     </div>
//   );
// }
