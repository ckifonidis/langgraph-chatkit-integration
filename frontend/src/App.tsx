import { useCallback } from "react";
import Home from "./components/Home";
import { useColorScheme } from "./hooks/useColorScheme";
import { PreferencesProvider } from "./contexts/PreferencesContext";

export default function App() {
  const { scheme, setScheme } = useColorScheme();
  const handleThemeChange = useCallback(
    (value: "light" | "dark") => {
      setScheme(value);
    },
    [setScheme]
  );

  return (
    <PreferencesProvider>
      <Home scheme={scheme} handleThemeChange={handleThemeChange} />
    </PreferencesProvider>
  );
}
