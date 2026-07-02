import SearchForm from "@/components/SearchForm";
import Pipeline from "@/components/Pipeline";

export default function Home() {
  return (
    <div className="flex flex-col items-center px-4 py-20 min-h-[80vh]">
      <SearchForm />

      <div className="w-full max-w-6xl mt-20 border-t border-white/10 pt-16">
        <Pipeline />
      </div>
    </div>
  );
}

