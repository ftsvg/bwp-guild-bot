"use strict";

const PLAYER_CHART_COLORS = {
    first: "#2ecc71",
    topFive: "#1f8b4c",
    twoOrMore: "#1685f8",
    belowTwo: "#f32c55",
};

const GUILD_CHART_COLORS = [
    "#663399",
    "#8262BB",
    "#9E90DD",
    "#BABFFF",
    "#6E73BC",
    "#222779",
    "#392B84",
    "#4F2F8E",
];

function readJsonData(elementId) {
    const element = document.getElementById(elementId);

    if (!element) {
        return [];
    }

    try {
        const data = JSON.parse(element.textContent);

        if (!Array.isArray(data)) {
            console.error(`Data in #${elementId} must be an array.`);
            return [];
        }

        return data;
    } catch (error) {
        console.error(`Unable to parse data from #${elementId}:`, error);
        return [];
    }
}

function normalizePlayers(rawData) {
    return rawData
        .filter((player) => {
            const username = player?.username;
            const starsGained = Number(player?.stars_gained);

            return (
                typeof username === "string" &&
                username.trim().length > 0 &&
                Number.isFinite(starsGained)
            );
        })
        .map((player) => {
            return {
                username: player.username.trim(),
                starsGained: Number(player.stars_gained),
            };
        })
        .sort((firstPlayer, secondPlayer) => {
            return secondPlayer.starsGained - firstPlayer.starsGained;
        });
}

function normalizeGuilds(rawData) {
    return rawData
        .filter((guild) => {
            const name = guild?.name;
            const gainedXp = Number(guild?.gained_xp);

            return (
                typeof name === "string" &&
                name.trim().length > 0 &&
                Number.isFinite(gainedXp)
            );
        })
        .map((guild) => {
            return {
                name: guild.name.trim(),
                gainedXp: Number(guild.gained_xp),
            };
        })
        .sort((firstGuild, secondGuild) => {
            return secondGuild.gainedXp - firstGuild.gainedXp;
        });
}

function getPlayerColor(index, starsGained) {
    if (index === 0) {
        return PLAYER_CHART_COLORS.first;
    }

    if (index < 5) {
        return PLAYER_CHART_COLORS.topFive;
    }

    if (starsGained >= 2) {
        return PLAYER_CHART_COLORS.twoOrMore;
    }

    return PLAYER_CHART_COLORS.belowTwo;
}

function getGuildColor(index) {
    return GUILD_CHART_COLORS[
        index % GUILD_CHART_COLORS.length
    ];
}

function formatStars(value) {
    return Number(value)
        .toFixed(2)
        .replace(/\.?0+$/, "");
}

function formatXp(value) {
    return new Intl.NumberFormat("en-US", {
        maximumFractionDigits: 0,
    }).format(Number(value));
}

function createPlayerXpChart(canvas, players) {
    const usernames = players.map(
        (player) => player.username,
    );

    const starValues = players.map(
        (player) => player.starsGained,
    );

    const barColors = players.map(
        (player, index) => {
            return getPlayerColor(
                index,
                player.starsGained,
            );
        },
    );

    return new Chart(canvas, {
        type: "bar",

        data: {
            labels: usernames,

            datasets: [
                {
                    label: "Stars gained",
                    data: starValues,

                    backgroundColor: barColors,
                    borderColor: barColors,
                    borderWidth: 1,

                    borderRadius: {
                        topLeft: 2,
                        topRight: 2,
                    },

                    borderSkipped: false,

                    categoryPercentage: 0.96,
                    barPercentage: 0.88,
                    maxBarThickness: 24,

                    hoverBackgroundColor: barColors,
                    hoverBorderColor: "#ffffff",
                    hoverBorderWidth: 1,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            animation: {
                duration: 500,
                easing: "easeOutQuart",
            },

            layout: {
                padding: {
                    top: 8,
                    right: 4,
                    bottom: 0,
                    left: 0,
                },
            },

            interaction: {
                mode: "nearest",
                axis: "x",
                intersect: true,
            },

            plugins: {
                legend: {
                    display: false,
                },

                tooltip: {
                    enabled: true,
                    displayColors: true,

                    backgroundColor: "rgba(15, 23, 42, 0.97)",
                    titleColor: "#f8fafc",
                    bodyColor: "#cbd5e1",

                    borderColor: "rgba(148, 163, 184, 0.25)",
                    borderWidth: 1,

                    padding: 10,
                    cornerRadius: 6,

                    titleFont: {
                        size: 13,
                        weight: "600",
                    },

                    bodyFont: {
                        size: 12,
                    },

                    callbacks: {
                        title(context) {
                            if (context.length === 0) {
                                return "";
                            }

                            return usernames[
                                context[0].dataIndex
                            ];
                        },

                        label(context) {
                            const stars = Number(context.parsed.y);

                            return `Stars gained: ${formatStars(stars)}`;
                        },

                        afterLabel(context) {
                            return `Position: #${context.dataIndex + 1}`;
                        },
                    },
                },
            },

            scales: {
                x: {
                    offset: true,

                    border: {
                        display: false,
                    },

                    grid: {
                        display: false,
                    },

                    ticks: {
                        autoSkip: false,
                        minRotation: 45,
                        maxRotation: 45,

                        color: "#cbd5e1",
                        padding: 8,

                        font: {
                            size: 10,
                            weight: "500",
                        },
                    },
                },

                y: {
                    beginAtZero: true,
                    grace: "6%",

                    border: {
                        display: false,
                    },

                    grid: {
                        color: "rgba(148, 163, 184, 0.11)",
                        drawTicks: false,
                    },

                    ticks: {
                        color: "#94a3b8",
                        padding: 8,

                        font: {
                            size: 10,
                        },

                        callback(value) {
                            return formatStars(value);
                        },
                    },

                    title: {
                        display: true,
                        text: "Stars gained",

                        color: "#94a3b8",

                        font: {
                            size: 11,
                            weight: "600",
                        },
                    },
                },
            },
        },
    });
}

function createGuildXpChart(canvas, guilds) {
    const guildNames = guilds.map(
        (guild) => guild.name,
    );

    const xpValues = guilds.map(
        (guild) => guild.gainedXp,
    );

    const barColors = guilds.map(
        (_, index) => getGuildColor(index),
    );

    return new Chart(canvas, {
        type: "bar",

        data: {
            labels: guildNames,

            datasets: [
                {
                    label: "Guild XP gained",
                    data: xpValues,

                    backgroundColor: barColors,
                    borderColor: barColors,
                    borderWidth: 1,

                    borderRadius: {
                        topLeft: 4,
                        topRight: 4,
                    },

                    borderSkipped: false,

                    barThickness: "flex",
                    categoryPercentage: 0.8,
                    barPercentage: 0.9,
                    maxBarThickness: 160,

                    hoverBackgroundColor: barColors,
                    hoverBorderColor: "#ffffff",
                    hoverBorderWidth: 1,
                },
            ],
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            animation: {
                duration: 500,
                easing: "easeOutQuart",
            },

            layout: {
                padding: {
                    top: 8,
                    right: 8,
                    bottom: 0,
                    left: 0,
                },
            },

            interaction: {
                mode: "nearest",
                axis: "x",
                intersect: true,
            },

            plugins: {
                legend: {
                    display: false,
                },

                tooltip: {
                    enabled: true,
                    displayColors: true,

                    backgroundColor: "rgba(15, 23, 42, 0.97)",
                    titleColor: "#f8fafc",
                    bodyColor: "#cbd5e1",

                    borderColor: "rgba(148, 163, 184, 0.25)",
                    borderWidth: 1,

                    padding: 10,
                    cornerRadius: 6,

                    titleFont: {
                        size: 13,
                        weight: "600",
                    },

                    bodyFont: {
                        size: 12,
                    },

                    callbacks: {
                        title(context) {
                            if (context.length === 0) {
                                return "";
                            }

                            return guildNames[
                                context[0].dataIndex
                            ];
                        },

                        label(context) {
                            const gainedXp = Number(
                                context.parsed.y,
                            );

                            return `XP gained: ${formatXp(gainedXp)}`;
                        },

                        afterLabel(context) {
                            return `Position: #${context.dataIndex + 1}`;
                        },
                    },
                },
            },

            scales: {
                x: {
                    offset: true,

                    border: {
                        display: false,
                    },

                    grid: {
                        display: false,
                    },

                    ticks: {
                        autoSkip: false,
                        minRotation: 45,
                        maxRotation: 45,

                        color: "#cbd5e1",
                        padding: 8,

                        font: {
                            size: 10,
                            weight: "500",
                        },
                    },
                },

                y: {
                    beginAtZero: true,
                    grace: "6%",

                    border: {
                        display: false,
                    },

                    grid: {
                        color: "rgba(148, 163, 184, 0.11)",
                        drawTicks: false,
                    },

                    ticks: {
                        color: "#94a3b8",
                        padding: 8,

                        font: {
                            size: 10,
                        },

                        callback(value) {
                            return formatXp(value);
                        },
                    },

                    title: {
                        display: true,
                        text: "Guild XP gained",

                        color: "#94a3b8",

                        font: {
                            size: 11,
                            weight: "600",
                        },
                    },
                },
            },
        },
    });
}

function initializePlayerXpChart() {
    const canvas = document.getElementById("xp-chart");

    if (!(canvas instanceof HTMLCanvasElement)) {
        return;
    }

    const rawData = readJsonData("xp-chart-data");
    const players = normalizePlayers(rawData);

    if (players.length === 0) {
        return;
    }

    createPlayerXpChart(canvas, players);
}

function initializeGuildXpChart() {
    const canvas = document.getElementById(
        "guild-xp-chart",
    );

    if (!(canvas instanceof HTMLCanvasElement)) {
        return;
    }

    const rawData = readJsonData(
        "guild-xp-chart-data",
    );

    const guilds = normalizeGuilds(rawData);

    if (guilds.length === 0) {
        return;
    }

    createGuildXpChart(canvas, guilds);
}

function initializeCharts() {
    if (typeof Chart === "undefined") {
        console.error("Chart.js has not loaded.");
        return;
    }

    initializePlayerXpChart();
    initializeGuildXpChart();
}

document.addEventListener(
    "DOMContentLoaded",
    initializeCharts,
);
