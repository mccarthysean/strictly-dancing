// Re-export API types from generated file
export type * from '@/types/api.gen';

// Import paths type for type-safe API calls
import type { paths } from '@/types/api.gen';

// Helper types for extracting request/response types
type PathMethods = {
  [P in keyof paths]: paths[P];
};

// Get response type for a specific endpoint and method
export type ApiResponse<
  Path extends keyof paths,
  Method extends keyof PathMethods[Path]
> = PathMethods[Path][Method] extends { responses: infer R }
  ? R extends { 200: { content: { 'application/json': infer T } } }
    ? T
    : R extends { 201: { content: { 'application/json': infer T } } }
      ? T
      : never
  : never;

// Get request body type for a specific endpoint and method
export type ApiRequestBody<
  Path extends keyof paths,
  Method extends keyof PathMethods[Path]
> = PathMethods[Path][Method] extends {
  requestBody: { content: { 'application/json': infer T } };
}
  ? T
  : never;

// Get query params type for a specific endpoint and method
export type ApiQueryParams<
  Path extends keyof paths,
  Method extends keyof PathMethods[Path]
> = PathMethods[Path][Method] extends { parameters: { query?: infer Q } }
  ? Q
  : never;

// Get path params type for a specific endpoint and method
export type ApiPathParams<
  Path extends keyof paths,
  Method extends keyof PathMethods[Path]
> = PathMethods[Path][Method] extends { parameters: { path?: infer P } }
  ? P
  : never;
