import { Navigate, Route, Routes } from "react-router";
import { useAuth } from "./auth/AuthProvider";
import { homePath } from "./auth/session";
import { Layout } from "./components/Layout";
import { RequireRole } from "./components/RequireRole";
import { ClassPage } from "./features/admin/ClassPage";
import { ClassesPage } from "./features/admin/ClassesPage";
import { SummaryPage } from "./features/admin/SummaryPage";
import { UserPage } from "./features/admin/UserPage";
import { UsersPage } from "./features/admin/UsersPage";
import { LoginPage } from "./features/login/LoginPage";
import { AssignmentPage, AssignmentQuestionPage, NewAssignmentPage } from "./features/teacher/AssignmentPage";
import { AssignmentsPage } from "./features/teacher/AssignmentsPage";
import { GeneratePage } from "./features/teacher/GeneratePage";
import { NewQuestionPage, QuestionPage } from "./features/teacher/QuestionPage";
import { QuestionsPage } from "./features/teacher/QuestionsPage";

function HomeRedirect() {
  const { auth } = useAuth();
  return <Navigate to={auth ? homePath(auth.user.role) : "/login"} replace />;
}

function ComingSoon() {
  return <p className="text-sm text-slate-500">This section is not built yet.</p>;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<Layout />}>
        <Route path="/admin" element={<RequireRole role="admin"><Navigate to="/admin/users" replace /></RequireRole>} />
        <Route path="/admin/users" element={<RequireRole role="admin"><UsersPage /></RequireRole>} />
        <Route path="/admin/users/:id" element={<RequireRole role="admin"><UserPage /></RequireRole>} />
        <Route path="/admin/classes" element={<RequireRole role="admin"><ClassesPage /></RequireRole>} />
        <Route path="/admin/classes/:id" element={<RequireRole role="admin"><ClassPage /></RequireRole>} />
        <Route
          path="/admin/classes/:cid/assignments/:aid"
          element={<RequireRole role="admin"><SummaryPage /></RequireRole>}
        />
        <Route path="/teacher" element={<RequireRole role="teacher"><Navigate to="/teacher/assignments" replace /></RequireRole>} />
        <Route path="/teacher/questions" element={<RequireRole role="teacher"><QuestionsPage /></RequireRole>} />
        <Route path="/teacher/questions/new" element={<RequireRole role="teacher"><NewQuestionPage /></RequireRole>} />
        <Route path="/teacher/questions/:id" element={<RequireRole role="teacher"><QuestionPage /></RequireRole>} />
        <Route path="/teacher/generate" element={<RequireRole role="teacher"><GeneratePage /></RequireRole>} />
        <Route path="/teacher/assignments" element={<RequireRole role="teacher"><AssignmentsPage /></RequireRole>} />
        <Route path="/teacher/assignments/new" element={<RequireRole role="teacher"><NewAssignmentPage /></RequireRole>} />
        <Route path="/teacher/assignments/:id" element={<RequireRole role="teacher"><AssignmentPage /></RequireRole>} />
        <Route
          path="/teacher/assignments/:id/questions/:qid"
          element={<RequireRole role="teacher"><AssignmentQuestionPage /></RequireRole>}
        />
        <Route path="/student/*" element={<RequireRole role="student"><ComingSoon /></RequireRole>} />
      </Route>
      <Route path="*" element={<HomeRedirect />} />
    </Routes>
  );
}
