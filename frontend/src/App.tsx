import "./App.css";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import AppLayout from "./layout/AppLayout";
import HomeCoachPage from "./pages/HomeCoachPage";
import CoachAiPage from "./pages/CoachAiPage";
import WeekPlannerPage from "./pages/WeekPlannerPage";
import GroupsPage from "./pages/GroupsPage";
import AthletesPage from "./pages/AthletesPage";
import WeekDashboardPage from "./pages/WeekDashboardPage";
import TemplatesCatalogPage from "./pages/TemplatesCatalogPage";
import TemplateDetailPage from "./pages/TemplateDetailPage";
import TemplateEditorPage from "./pages/TemplateEditorPage";
import SessionsCatalogPage from "./pages/SessionsCatalogPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home" element={<HomeCoachPage />} />
          <Route path="/library/sessions" element={<SessionsCatalogPage />} />
          <Route path="/planner/week" element={<WeekPlannerPage />} />
          <Route path="/athletes" element={<AthletesPage />} />
          <Route path="/groups" element={<GroupsPage />} />
          <Route path="/coach-ai" element={<CoachAiPage />} />
          <Route path="/templates" element={<TemplatesCatalogPage />} />
          <Route path="/templates/new" element={<TemplateEditorPage />} />
          <Route path="/templates/:id" element={<TemplateDetailPage />} />
          <Route path="/dashboard/week" element={<WeekDashboardPage />} />
          <Route path="*" element={<Navigate to="/home" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
