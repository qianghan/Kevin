import mongoose, { Document, Schema, Model } from 'mongoose';

// Define common properties for all user types
export interface BaseUser {
  email: string;
  name: string;
  image?: string;
  emailVerified?: Date;
  createdAt: Date;
  updatedAt: Date;
}

// Define Student specific properties
export interface StudentUser extends BaseUser {
  role: 'student';
  parentIds: mongoose.Types.ObjectId[];
}

// Define Parent specific properties
export interface ParentUser extends BaseUser {
  role: 'parent';
  studentIds: mongoose.Types.ObjectId[];
  partnerIds: mongoose.Types.ObjectId[];
}

// Combined user type for the document
export type UserType = StudentUser | ParentUser;

// Interface for the Mongoose document
export interface UserDocument extends Document, BaseUser {
  role: 'student' | 'parent';
  parentIds?: mongoose.Types.ObjectId[];
  studentIds?: mongoose.Types.ObjectId[];
  partnerIds?: mongoose.Types.ObjectId[];
}

// Define the schema
const UserSchema = new Schema<UserDocument>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
    },
    name: {
      type: String,
      required: true,
    },
    image: {
      type: String,
    },
    emailVerified: {
      type: Date,
    },
    role: {
      type: String,
      enum: ['student', 'parent'],
      required: true,
    },
    // Parent references for students
    parentIds: {
      type: [Schema.Types.ObjectId],
      ref: 'User',
      default: [],
    },
    // Student references for parents
    studentIds: {
      type: [Schema.Types.ObjectId],
      ref: 'User',
      default: [],
    },
    // Partner references for parents (other parents)
    partnerIds: {
      type: [Schema.Types.ObjectId],
      ref: 'User',
      default: [],
    },
  },
  {
    timestamps: true,
  }
);

// Define static methods
// Find or create a user by provider info (for OAuth)
UserSchema.statics.findOrCreateByProvider = async function (
  providerData: { email: string; name: string; image?: string; provider: string },
) {
  const user = await this.findOne({ email: providerData.email });
  
  if (user) {
    return user;
  }
  
  // Create a new user with default role "parent" 
  // (can be changed during registration flow)
  return this.create({
    email: providerData.email,
    name: providerData.name,
    image: providerData.image,
    role: 'parent', // Default role
  });
};

// Add a student to a parent
UserSchema.methods.addStudent = async function (studentId: mongoose.Types.ObjectId) {
  if (this.role !== 'parent') {
    throw new Error('Only parents can add students');
  }
  
  if (!this.studentIds.includes(studentId)) {
    this.studentIds.push(studentId);
    await this.save();
    
    // Update the student's parent list
    const studentModel = mongoose.model<UserDocument>('User');
    await studentModel.findByIdAndUpdate(
      studentId,
      { $addToSet: { parentIds: this._id } }
    );
  }
  
  return this;
};

// Add a partner to a parent
UserSchema.methods.addPartner = async function (partnerId: mongoose.Types.ObjectId) {
  if (this.role !== 'parent') {
    throw new Error('Only parents can add partners');
  }
  
  if (!this.partnerIds.includes(partnerId)) {
    this.partnerIds.push(partnerId);
    await this.save();
    
    // Update the partner's partner list
    const partnerModel = mongoose.model<UserDocument>('User');
    await partnerModel.findByIdAndUpdate(
      partnerId,
      { $addToSet: { partnerIds: this._id } }
    );
  }
  
  return this;
};

// Interface for the User model with static methods
interface UserModel extends Model<UserDocument> {
  findOrCreateByProvider(providerData: { 
    email: string; 
    name: string; 
    image?: string; 
    provider: string 
  }): Promise<UserDocument>;
}

// Check if the model exists before creating it to avoid "OverwriteModelError"
const User = (mongoose.models.User as UserModel) || 
  mongoose.model<UserDocument, UserModel>('User', UserSchema);

export default User; 