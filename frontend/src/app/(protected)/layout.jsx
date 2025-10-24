import Navbar from "@/components/navbar/Navbar";

export default function ProtectedLayout({ children }) {
  return (
    <>
      <Navbar />
      {children}
    </>
  );
}
