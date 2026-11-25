import SiteHeader from "@/components/SiteHeader";
import SiteFooter from "@/components/SiteFooter";
import UrlQrGenerator from "@/components/UrlQrGenerator";

export const metadata = {
  title: "URL → QR | Face QR Studio",
};

export default function UrlQrPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      <section className="hero-glow">
        <div className="mx-auto max-w-3xl px-4 pb-6 pt-10 text-center sm:px-6 sm:pt-16">
          <h1 className="text-3xl font-extrabold tracking-tight sm:text-5xl">
            URL →{" "}
            <span className="bg-gradient-to-r from-indigo-600 to-violet-500 bg-clip-text text-transparent">
              QR Code
            </span>
          </h1>
          <p className="mt-3 text-slate-600 dark:text-slate-400">
            Link type pannunga, scan aagura QR udane generate aagum.
          </p>
        </div>
      </section>

      <main className="mx-auto max-w-5xl px-4 pb-16 sm:px-6">
        <UrlQrGenerator />
      </main>

      <SiteFooter />
    </div>
  );
}