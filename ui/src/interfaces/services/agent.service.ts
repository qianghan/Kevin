/**
 * Agent Service Interface
 * 
 * Defines the contract for AI agent-related operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to agent management.
 */

export interface Agent {
  id: string;
  name: string;
  description: string;
  version: string;
  capabilities: AgentCapability[];
  icon?: string;
  publisher: string;
  isInstalled: boolean;
  installDate?: string;
  isEnabled: boolean;
  rating?: number;
  reviews?: number;
  tags: string[];
  category: AgentCategory;
  requiresEntitlement: boolean;
  pricing?: AgentPricing;
}

export type AgentCategory = 
  | 'education' 
  | 'productivity' 
  | 'creativity' 
  | 'communication'
  | 'utility'
  | 'entertainment';

export interface AgentCapability {
  id: string;
  name: string;
  description: string;
  icon?: string;
}

export interface AgentPricing {
  type: 'free' | 'paid' | 'subscription';
  amount?: number;
  currency?: string;
  period?: 'monthly' | 'yearly';
}

export interface AgentFilter {
  search?: string;
  categories?: AgentCategory[];
  capabilities?: string[];
  installed?: boolean;
  enabled?: boolean;
  requiresEntitlement?: boolean;
  pricingType?: AgentPricing['type'][];
}

export interface AgentInstallOptions {
  enableAfterInstall?: boolean;
}

export interface IAgentService {
  /**
   * Get all available agents
   * @returns Promise resolving to array of agents
   */
  getAvailableAgents(): Promise<Agent[]>;
  
  /**
   * Get all installed agents
   * @returns Promise resolving to array of installed agents
   */
  getInstalledAgents(): Promise<Agent[]>;
  
  /**
   * Get a specific agent by ID
   * @param agentId Agent ID
   * @returns Promise resolving to the agent
   */
  getAgent(agentId: string): Promise<Agent>;
  
  /**
   * Install an agent
   * @param agentId Agent ID
   * @param options Installation options
   * @returns Promise resolving to the installed agent
   */
  installAgent(agentId: string, options?: AgentInstallOptions): Promise<Agent>;
  
  /**
   * Uninstall an agent
   * @param agentId Agent ID
   * @returns Promise that resolves when the agent is uninstalled
   */
  uninstallAgent(agentId: string): Promise<void>;
  
  /**
   * Enable an installed agent
   * @param agentId Agent ID
   * @returns Promise resolving to the enabled agent
   */
  enableAgent(agentId: string): Promise<Agent>;
  
  /**
   * Disable an installed agent
   * @param agentId Agent ID
   * @returns Promise resolving to the disabled agent
   */
  disableAgent(agentId: string): Promise<Agent>;
  
  /**
   * Search and filter agents
   * @param filter Filter criteria
   * @returns Promise resolving to filtered agents
   */
  searchAgents(filter: AgentFilter): Promise<Agent[]>;
  
  /**
   * Get recommended agents based on user profile
   * @returns Promise resolving to recommended agents
   */
  getRecommendedAgents(): Promise<Agent[]>;
  
  /**
   * Get an agent's capabilities
   * @param agentId Agent ID
   * @returns Promise resolving to agent capabilities
   */
  getAgentCapabilities(agentId: string): Promise<AgentCapability[]>;
  
  /**
   * Check if user has entitlement for an agent
   * @param agentId Agent ID
   * @returns Promise resolving to entitlement status
   */
  checkAgentEntitlement(agentId: string): Promise<boolean>;
  
  /**
   * Purchase an agent entitlement
   * @param agentId Agent ID
   * @returns Promise resolving to purchase success status
   */
  purchaseAgentEntitlement(agentId: string): Promise<boolean>;
} 