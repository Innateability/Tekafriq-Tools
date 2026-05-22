from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ---------------------------------------------------------------------------
# Association Tables
# ---------------------------------------------------------------------------

opportunity_tracker_assignments = db.Table(
    "opportunity_tracker_assignments",
    db.Column(
        "opportunity_tracker_id",
        db.Integer,
        db.ForeignKey("opportunity_trackers.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    db.Column(
        "authentication_id",
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


# ---------------------------------------------------------------------------
# Core / Shared Models
# ---------------------------------------------------------------------------

class EmployeeEmail(db.Model):
    """
    Pre-approved email list used during registration.
    `role` column added to support the performance-management app;
    defaults to None so the CRM app rows are unaffected.
    """
    __tablename__ = "employee_emails"

    id         = db.Column(db.Integer, primary_key=True)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    department = db.Column(db.String(150), nullable=False)
    # Added by performance-management app (nullable so CRM records still work)
    role       = db.Column(db.String(150), nullable=True)


class Authentication(db.Model):
    """
    Single authentication record shared by both apps.
    Relationships from both apps are merged here.
    `role` is NOT NULL — all registration flows must supply a value.
    """
    __tablename__ = "authentications"

    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    name     = db.Column(db.String(200), nullable=False)
    # nullable=False (performance-management requirement); CRM already stored a role
    role     = db.Column(db.String(50), nullable=False)

    # ---- profile relationships ----
    employee      = db.relationship("Employee",      back_populates="authentication", uselist=False)
    team_leader   = db.relationship("TeamLeader",    back_populates="authentication", uselist=False)
    administrator = db.relationship("Administrator", back_populates="authentication", uselist=False)

    # ---- CRM app relationships ----
    opportunity_trackers = db.relationship(
        "OpportunityTracker",
        secondary=opportunity_tracker_assignments,
        back_populates="assigned_to",
    )

    # ---- Performance-management app relationships ----
    objectives       = db.relationship("Objective",      back_populates="assigned_to", cascade="all, delete-orphan")
    admin_objectives = db.relationship("AdminObjective", back_populates="assigned_to", cascade="all, delete-orphan")
    auth_reviewed    = db.relationship("AuthReviewed",   back_populates="authentication", uselist=False)


class Department(db.Model):
    """
    Shared department record.
    `team_leader` relationship added for the performance-management app.
    """
    __tablename__ = "departments"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)

    administrator_id = db.Column(
        db.Integer,
        db.ForeignKey("administrators.id", ondelete="SET NULL"),
        nullable=True,
    )

    administrator = db.relationship("Administrator", back_populates="departments")
    employees     = db.relationship("Employee",      back_populates="department", cascade="all")

    # Performance-management app: one team leader per department
    team_leader = db.relationship(
        "TeamLeader",
        back_populates="department",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Employee(db.Model):
    __tablename__ = "employees"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
    )
    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    department     = db.relationship("Department",     back_populates="employees")
    authentication = db.relationship("Authentication", back_populates="employee")


class Administrator(db.Model):
    __tablename__ = "administrators"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    authentication = db.relationship("Authentication", back_populates="administrator")
    departments    = db.relationship("Department",     back_populates="administrator")

    # Performance-management app
    admin_objectives = db.relationship("AdminObjective", back_populates="assigned_by", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# CRM App Models
# ---------------------------------------------------------------------------

class Comment(db.Model):
    __tablename__ = "comments"

    id          = db.Column(db.Integer, primary_key=True)
    comment     = db.Column(db.String, nullable=False)
    timestamp   = db.Column(db.DateTime, nullable=False)
    author      = db.Column(db.String, nullable=False)

    opportunity_tracker_id = db.Column(
        db.Integer,
        db.ForeignKey("opportunity_trackers.id", ondelete="CASCADE"),
    )
    opportunity_tracker = db.relationship("OpportunityTracker", back_populates="comments")


class OpportunityTracker(db.Model):
    __tablename__ = "opportunity_trackers"

    id                 = db.Column(db.Integer, primary_key=True)
    firm               = db.Column(db.String(200), nullable=False)
    year               = db.Column(db.Integer,     nullable=False)
    industry           = db.Column(db.String(200), nullable=False)
    modules            = db.Column(db.JSON,        default=list)
    reffered_by        = db.Column(db.String(200), nullable=True,  default="")
    deal_size          = db.Column(db.Integer,     nullable=True,  default=0)
    opportunity_stage  = db.Column(db.String(200), nullable=False, default="Lead")
    exp_closure_date   = db.Column(db.DateTime,    nullable=True,  default=None)
    customer_party     = db.Column(db.String(200), nullable=True,  default="")
    status             = db.Column(db.String(200), nullable=True,  default="Lead")

    assigned_to = db.relationship(
        "Authentication",
        secondary=opportunity_tracker_assignments,
        back_populates="opportunity_trackers",
    )
    comments = db.relationship("Comment", back_populates="opportunity_tracker")


# ---------------------------------------------------------------------------
# Performance-Management App Models
# ---------------------------------------------------------------------------

class TeamLeader(db.Model):
    __tablename__ = "team_leaders"

    id   = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)

    department_id = db.Column(
        db.Integer,
        db.ForeignKey("departments.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    authentication_id = db.Column(
        db.Integer,
        db.ForeignKey("authentications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    department     = db.relationship("Department",     back_populates="team_leader")
    authentication = db.relationship("Authentication", back_populates="team_leader")
    objectives     = db.relationship("Objective",      back_populates="assigned_by", cascade="all, delete-orphan")


class ObjectiveBatch(db.Model):
    __tablename__ = "objective_batches"

    id         = db.Column(db.Integer,  primary_key=True)
    title      = db.Column(db.String(200), nullable=False)
    year       = db.Column(db.Integer,  nullable=False)
    completed  = db.Column(db.Boolean,  nullable=False)
    duration   = db.Column(db.Integer)
    created_at = db.Column(db.DateTime)
    deadline   = db.Column(db.DateTime)
    end        = db.Column(db.DateTime)
    start      = db.Column(db.DateTime)
    active     = db.Column(db.Boolean)

    admin_objectives = db.relationship("AdminObjective", back_populates="batch", cascade="all, delete-orphan")
    objectives       = db.relationship("Objective",      back_populates="batch", cascade="all, delete-orphan")


class Objective(db.Model):
    __tablename__ = "objectives"

    id          = db.Column(db.Integer, primary_key=True)
    objective   = db.Column(db.String,  nullable=False)
    category    = db.Column(db.String,  nullable=False)
    score_range = db.Column(db.Integer, nullable=False)
    weight      = db.Column(db.Integer, nullable=False)
    private     = db.Column(db.Boolean, nullable=False)

    assigned_by_id = db.Column(db.Integer, db.ForeignKey("team_leaders.id",    ondelete="CASCADE"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("authentications.id", ondelete="CASCADE"), nullable=False)
    batch_id       = db.Column(db.Integer, db.ForeignKey("objective_batches.id", ondelete="CASCADE"), nullable=False)

    assigned_by = db.relationship("TeamLeader",     back_populates="objectives")
    assigned_to = db.relationship("Authentication", back_populates="objectives")
    batch       = db.relationship("ObjectiveBatch", back_populates="objectives")

    review = db.relationship(
        "Review",
        back_populates="objective",
        uselist=False,
        cascade="all, delete-orphan",
    )
    open_objectives_review = db.relationship(
        "ReviewOpenObjective",
        back_populates="objective",
        uselist=False,
        cascade="all, delete-orphan",
    )
    messages = db.relationship(
        "Messages",
        back_populates="objective",
        uselist=False,
        cascade="all, delete-orphan",
    )
    auth_reviewed = db.relationship(
        "AuthReviewed",
        back_populates="objective",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AdminObjective(db.Model):
    __tablename__ = "admin_objectives"

    id          = db.Column(db.Integer, primary_key=True)
    objective   = db.Column(db.String,  nullable=False)
    category    = db.Column(db.String,  nullable=False)
    score_range = db.Column(db.Integer, nullable=False)
    weight      = db.Column(db.Integer, nullable=False)
    private     = db.Column(db.Boolean, nullable=False)

    batch_id       = db.Column(db.Integer, db.ForeignKey("objective_batches.id",  ondelete="CASCADE"), nullable=False)
    assigned_by_id = db.Column(db.Integer, db.ForeignKey("administrators.id",     ondelete="CASCADE"), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("authentications.id",    ondelete="CASCADE"), nullable=False)

    batch       = db.relationship("ObjectiveBatch", back_populates="admin_objectives")
    assigned_by = db.relationship("Administrator",  back_populates="admin_objectives")
    assigned_to = db.relationship("Authentication", back_populates="admin_objectives")

    admin_review = db.relationship(
        "AdminReview",
        back_populates="admin_objective",
        uselist=False,
        cascade="all, delete-orphan",
    )
    open_objectives_review = db.relationship(
        "ReviewOpenObjective",
        back_populates="admin_objective",
        uselist=False,
        cascade="all, delete-orphan",
    )
    messages = db.relationship("Messages", back_populates="admin_objective")
    auth_reviewed = db.relationship(
        "AuthReviewed",
        back_populates="admin_objective",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Review(db.Model):
    __tablename__ = "reviews"

    id            = db.Column(db.Integer, primary_key=True)
    review        = db.Column(db.String(500), nullable=False)
    score         = db.Column(db.Float,   nullable=False)
    weighted_score = db.Column(db.Float,  nullable=False)

    objective_id = db.Column(
        db.Integer,
        db.ForeignKey("objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    objective = db.relationship("Objective", back_populates="review")
    feedback  = db.relationship(
        "Feedback",
        back_populates="review",
        uselist=False,
        cascade="all, delete-orphan",
    )


class AdminReview(db.Model):
    __tablename__ = "admin_reviews"

    id             = db.Column(db.Integer, primary_key=True)
    review         = db.Column(db.String(500), nullable=False)
    score          = db.Column(db.Float,   nullable=False)
    weighted_score = db.Column(db.Float,   nullable=False)

    admin_objective_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )

    admin_objective   = db.relationship("AdminObjective", back_populates="admin_review")
    employee_feedback = db.relationship(
        "AdminReviewFeedback",
        back_populates="admin_review",
        uselist=False,
        cascade="all, delete-orphan",
    )
    team_leader_feedback = db.relationship(
        "TeamLeaderFeedback",
        back_populates="admin_review",
        uselist=False,
        cascade="all, delete-orphan",
    )


class ReviewOpenObjective(db.Model):
    __tablename__ = "reviewopenobjectives"

    id             = db.Column(db.Integer, primary_key=True)
    review         = db.Column(db.String(500), nullable=False)
    score          = db.Column(db.Float,   nullable=False)
    weighted_score = db.Column(db.Float,   nullable=False)
    number_reviews = db.Column(db.Integer, nullable=False)

    objective_id = db.Column(
        db.Integer,
        db.ForeignKey("objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )
    objective = db.relationship("Objective", back_populates="open_objectives_review")

    admin_objective_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_objectives.id", ondelete="CASCADE"),
        unique=True,
        nullable=True,
    )
    admin_objective = db.relationship("AdminObjective", back_populates="open_objectives_review")


class AuthReviewed(db.Model):
    __tablename__ = "auth_reviewed"

    id    = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Float,   nullable=False)

    auth_id = db.Column(db.Integer, db.ForeignKey("authentications.id", ondelete="CASCADE"))
    authentication = db.relationship("Authentication", back_populates="auth_reviewed")

    objective_id = db.Column(db.Integer, db.ForeignKey("objectives.id", ondelete="CASCADE"))
    objective    = db.relationship("Objective", back_populates="auth_reviewed")

    admin_objective_id = db.Column(db.Integer, db.ForeignKey("admin_objectives.id", ondelete="CASCADE"))
    admin_objective    = db.relationship("AdminObjective", back_populates="auth_reviewed")


class Messages(db.Model):
    __tablename__ = "messages"

    id        = db.Column(db.Integer, primary_key=True)
    message   = db.Column(db.String,   nullable=False)
    status    = db.Column(db.String,   nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)

    objective_id = db.Column(db.Integer, db.ForeignKey("objectives.id",       ondelete="CASCADE"))
    admin_objective_id = db.Column(db.Integer, db.ForeignKey("admin_objectives.id", ondelete="CASCADE"))

    objective       = db.relationship("Objective",      back_populates="messages")
    admin_objective = db.relationship("AdminObjective", back_populates="messages")


class Feedback(db.Model):
    __tablename__ = "feedbacks"

    id       = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    review_id = db.Column(
        db.Integer,
        db.ForeignKey("reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    review = db.relationship("Review", back_populates="feedback")


class AdminReviewFeedback(db.Model):
    __tablename__ = "admin_review_feedbacks"

    id       = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    admin_review_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    admin_review = db.relationship("AdminReview", back_populates="employee_feedback")


class TeamLeaderFeedback(db.Model):
    __tablename__ = "team_leader_feedbacks"

    id       = db.Column(db.Integer, primary_key=True)
    feedback = db.Column(db.String(500), nullable=False)

    admin_review_id = db.Column(
        db.Integer,
        db.ForeignKey("admin_reviews.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    admin_review = db.relationship("AdminReview", back_populates="team_leader_feedback")