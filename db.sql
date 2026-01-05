"""CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) NOT NULL,
    mobile VARCHAR(10) UNIQUE NOT NULL,
    password VARCHAR(255),
    role ENUM('admin','user') DEFAULT 'user'
);

CREATE TABLE split_groups (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) UNIQUE NOT NULL,
    closed TINYINT(1) DEFAULT 0
);

CREATE TABLE split_group_members (
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    PRIMARY KEY (group_id, user_id),
    FOREIGN KEY (group_id) REFERENCES split_groups(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE split_expenses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    paid_by_id INT NOT NULL,  -- user_id
    description VARCHAR(200),
    total_paise BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES split_groups(id),
    FOREIGN KEY (paid_by_id) REFERENCES users(id)
);

CREATE TABLE split_shares (
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    share_paise BIGINT NOT NULL,
    PRIMARY KEY (expense_id, user_id),
    FOREIGN KEY (expense_id) REFERENCES split_expenses(id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE settlements (
    id INT PRIMARY KEY AUTO_INCREMENT,
    group_id INT NOT NULL,
    payer_id INT NOT NULL,
    receiver_id INT NOT NULL,
    amount_paise BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES split_groups(id),
    FOREIGN KEY (payer_id) REFERENCES users(id),
    FOREIGN KEY (receiver_id) REFERENCES users(id)
);
"""