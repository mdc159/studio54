type BoardActorMembership = {
  companyId: string;
  membershipRole: string | null;
  status: string;
};

type RequestActor = {
  type: "none" | "board" | "agent";
  source: "none" | "local_implicit" | "session" | "board_key" | "agent_jwt" | "agent_key";
  userId?: string;
  userName?: string | null;
  userEmail?: string | null;
  companyIds?: string[];
  memberships?: BoardActorMembership[];
  isInstanceAdmin?: boolean;
  keyId?: string;
  runId?: string;
  agentId?: string;
  companyId?: string;
};

declare global {
  namespace Express {
    interface Request {
      actor: RequestActor;
    }
  }
}

export {};
