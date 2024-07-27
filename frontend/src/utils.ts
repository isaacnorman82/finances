export function formatBalance(balance: string | number): string {
  // console.log("Formatting balance", balance);
  const numericBalance =
    typeof balance === "string" ? parseFloat(balance) : balance;
  const formattedBalance = `£${Math.abs(numericBalance).toFixed(2)}`;

  if (numericBalance < 0) {
    return `<span style="color: red">${formattedBalance}</span>`;
  }
  return formattedBalance;
}

export function formatDate(dateTime: string): string {
  if (!dateTime) return "N/A";

  // Parse the date
  const date = new Date(dateTime);

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0"); // Months are zero-based
  const year = date.getFullYear().toString();

  return `${day}/${month}/${year}`;
}

export const formatLastTransactionDate = (dateTime: string | null) => {
  if (!dateTime) return "N/A";

  // Parse the date
  const date = new Date(dateTime);
  const now = new Date();
  const diffTime = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

  return `${formatDate(dateTime)} (${diffDays} days ago)`;
};
