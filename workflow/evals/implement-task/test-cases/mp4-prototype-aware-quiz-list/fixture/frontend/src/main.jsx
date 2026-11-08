import React from "react";
import { createRoot } from "react-dom/client";
import { QuizList } from "./QuizList.jsx";
import { quizItems } from "./quiz-data.mjs";

createRoot(document.getElementById("root")).render(
  <QuizList items={quizItems} />,
);
