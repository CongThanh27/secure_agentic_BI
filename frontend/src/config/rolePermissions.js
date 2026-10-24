/** Mirrors agent_role_permissions seed policy (MySQL init). */
export const rolePermissions = {
  analyst: {
    catalogs: ['pg', 'mysql'],
    allowed: [
      'pg.public.regions',
      'pg.public.categories',
      'pg.public.products',
      'pg.public.orders',
      'pg.public.order_items',
      'mysql.agentic_bi.customer_profiles',
      'mysql.agentic_bi.customer_reviews',
    ],
    denied: [
      'pg.public.hr_payroll',
      'pg.public.api_keys_config',
      'pg.public.financial_transactions',
    ],
    canExportFile: false,
    maxRowLimit: 5000,
    canExecuteDdl: false,
    canAccessPii: false,
  },
  sales: {
    catalogs: ['pg', 'mysql'],
    allowed: [
      'pg.public.customers',
      'pg.public.products',
      'pg.public.orders',
      'pg.public.order_items',
      'pg.public.payments',
      'mysql.agentic_bi.customer_profiles',
    ],
    denied: ['pg.public.hr_payroll', 'pg.public.api_keys_config'],
    canExportFile: true,
    maxRowLimit: 2000,
    canExecuteDdl: false,
    canAccessPii: true,
  },
  support: {
    catalogs: ['mysql', 'pg'],
    allowed: [
      'mysql.agentic_bi.customer_profiles',
      'mysql.agentic_bi.support_tickets',
      'mysql.agentic_bi.customer_reviews',
      'pg.public.orders',
    ],
    denied: [
      'pg.public.hr_payroll',
      'pg.public.api_keys_config',
      'pg.public.financial_transactions',
    ],
    canExportFile: false,
    maxRowLimit: 1000,
    canExecuteDdl: false,
    canAccessPii: true,
  },
  hr: {
    catalogs: ['pg', 'mysql'],
    allowed: ['pg.public.employees', 'mysql.agentic_bi.agent_query_history'],
    denied: ['pg.public.api_keys_config', 'pg.public.financial_transactions'],
    canExportFile: false,
    maxRowLimit: 1000,
    canExecuteDdl: false,
    canAccessPii: true,
  },
  admin: {
    catalogs: ['pg', 'mysql'],
    allowed: ['* (all tables)'],
    denied: [],
    canExportFile: true,
    maxRowLimit: 10000,
    canExecuteDdl: true,
    canAccessPii: true,
  },
}

export const roles = Object.keys(rolePermissions)
