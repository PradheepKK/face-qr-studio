import SiteHeader from "@/components/SiteHeader";
import UrlQrGenerator from "@/components/UrlQrGenerator";

export const metadata = {
  title: "URL → QR | Face QR Studio",
};

export default function UrlQrPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-5xl space-y-6 px-4 py-10">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">URL → QR Code</h1>
          <p className="mt-2 text-slate-600 dark:text-slate-400">
            Link type pannunga, scan aagura QR generate aagum.
          </p>
        </div>
        <UrlQrGenerator />
      </main>
    </div>
  );
}