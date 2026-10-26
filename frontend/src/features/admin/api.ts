import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "../../api/client";
import { keys, prefixes } from "../../api/keys";
import type {
  ClassCreate,
  ClassDetail,
  ClassOut,
  ClassUpdate,
  Role,
  User,
  UserCreate,
  UserDetail,
  UserUpdate,
} from "../../api/types";

// Admin queries and mutations; cache updates follow frontend-admin §1.2.

export const useUsers = (role?: Role) =>
  useQuery({
    queryKey: keys.adminUsers(role),
    queryFn: ({ signal }) => apiFetch<User[]>(role ? `/admin/users?role=${role}` : "/admin/users", { signal }),
  });

export const useUser = (id: number) =>
  useQuery({
    queryKey: keys.adminUser(id),
    queryFn: ({ signal }) => apiFetch<UserDetail>(`/admin/users/${id}`, { signal }),
  });

export const useClasses = () =>
  useQuery({
    queryKey: keys.adminClasses(),
    queryFn: ({ signal }) => apiFetch<ClassOut[]>("/admin/classes", { signal }),
  });

export const useClass = (id: number) =>
  useQuery({
    queryKey: keys.adminClass(id),
    queryFn: ({ signal }) => apiFetch<ClassDetail>(`/admin/classes/${id}`, { signal }),
  });

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserCreate) => apiFetch<User>("/admin/users", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: prefixes.adminUsers }),
  });
}

export function useUpdateUser(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: UserUpdate) => apiFetch<User>(`/admin/users/${id}`, { method: "PATCH", body }),
    onSuccess: (user) => {
      // The response has no class list, so merge it into the cached detail.
      qc.setQueryData<UserDetail>(keys.adminUser(id), (prev) => (prev ? { ...prev, ...user } : prev));
      void qc.invalidateQueries({ queryKey: prefixes.adminUsers });
      void qc.invalidateQueries({ queryKey: prefixes.adminClass });
    },
  });
}

export function useDeleteUser(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>(`/admin/users/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.removeQueries({ queryKey: keys.adminUser(id) });
      void qc.invalidateQueries({ queryKey: prefixes.adminUsers });
      void qc.invalidateQueries({ queryKey: keys.adminClasses() });
      void qc.invalidateQueries({ queryKey: prefixes.adminClass });
    },
  });
}

export function useCreateClass() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ClassCreate) => apiFetch<ClassOut>("/admin/classes", { method: "POST", body }),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.adminClasses() }),
  });
}

export function useUpdateClass(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ClassUpdate) => apiFetch<ClassOut>(`/admin/classes/${id}`, { method: "PATCH", body }),
    onSuccess: (cls) => {
      // The response has no member lists, so merge it into the cached detail.
      qc.setQueryData<ClassDetail>(keys.adminClass(id), (prev) => (prev ? { ...prev, ...cls } : prev));
      void qc.invalidateQueries({ queryKey: keys.adminClasses() });
    },
  });
}

export function useDeleteClass(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => apiFetch<void>(`/admin/classes/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      qc.removeQueries({ queryKey: keys.adminClass(id) });
      void qc.invalidateQueries({ queryKey: keys.adminClasses() });
      void qc.invalidateQueries({ queryKey: prefixes.adminUser });
    },
  });
}

function useInvalidateMembership(classId: number) {
  const qc = useQueryClient();
  return () => {
    void qc.invalidateQueries({ queryKey: keys.adminClass(classId) });
    void qc.invalidateQueries({ queryKey: keys.adminClasses() });
    void qc.invalidateQueries({ queryKey: prefixes.adminUser });
  };
}

export function useAddMembers(classId: number) {
  const onSuccess = useInvalidateMembership(classId);
  return useMutation({
    mutationFn: (userIds: number[]) =>
      apiFetch<ClassDetail>(`/admin/classes/${classId}/members`, { method: "POST", body: { user_ids: userIds } }),
    onSuccess,
  });
}

export function useRemoveMember(classId: number) {
  const onSuccess = useInvalidateMembership(classId);
  return useMutation({
    mutationFn: (userId: number) =>
      apiFetch<void>(`/admin/classes/${classId}/members/${userId}`, { method: "DELETE" }),
    onSuccess,
  });
}
