import { quizCards } from "./quiz-list.mjs";

export function QuizList({ items }) {
  return (
    <main>
      <h1>My quizzes</h1>
      <div className="quiz-grid">
        {quizCards(items).map((card) => (
          <article key={card.id}>
            <h2>{card.title}</h2>
            <p>{card.className}</p>
            <a href={card.href}>{card.action}</a>
          </article>
        ))}
      </div>
    </main>
  );
}
