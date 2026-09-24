! rule: S19.4-007
! covers: do-concurrent-forall-index-scope
! covers: index-name-scalar-variable
! covers: implicit-rules-control-index-type
! covers: index-name-not-host-declaration
module scoping_kind_provider_index
  implicit none
  integer, parameter :: k2 = selected_int_kind(18)
end module

program scoping_19_3_19_5_index_scope_type
  use scoping_kind_provider_index, only: k2
  implicit integer(kind=k2) (p)
  integer :: checks
  integer :: i, k, m, host_idx
  integer :: dc_values(3), forall_stmt(3), forall_construct(3)
  integer :: implicit_kind, host_index_values(3), host_index_seen
  checks = 0
  i = 99
  k = 88
  m = 77
  host_idx = 555
  dc_values = -1
  forall_stmt = -2
  forall_construct = -3
  implicit_kind = -5
  host_index_values = -6
  host_index_seen = -7
  do concurrent (i = 1:3)
    dc_values(i) = i
  end do
  forall (k = 1:3) forall_stmt(k) = k + 10
  forall (m = 1:3)
    forall_construct(m) = m + 20
  end forall
  do concurrent (p = 1:1)
    implicit_kind = kind(p)
  end do
  block
    do concurrent (host_idx = 1:3)
      host_index_values(host_idx) = host_idx
    end do
    host_index_seen = host_idx
  end block
  if (any(dc_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:index_scope_type:do-concurrent-values'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:index_scope_type:do-concurrent-outer'
    error stop
  end if
  checks = checks + 1
  if (any(forall_stmt /= [11, 12, 13])) then
    write(*,'(a)') 'SCOPE:index_scope_type:forall-statement-values'
    error stop
  end if
  checks = checks + 1
  if (k /= 88) then
    write(*,'(a)') 'SCOPE:index_scope_type:forall-statement-outer'
    error stop
  end if
  checks = checks + 1
  if (any(forall_construct /= [21, 22, 23])) then
    write(*,'(a)') 'SCOPE:index_scope_type:forall-construct-values'
    error stop
  end if
  checks = checks + 1
  if (m /= 77) then
    write(*,'(a)') 'SCOPE:index_scope_type:forall-construct-outer'
    error stop
  end if
  checks = checks + 1
  if (implicit_kind /= k2) then
    write(*,'(a)') 'SCOPE:index_scope_type:implicit-kind'
    error stop
  end if
  checks = checks + 1
  if (any(host_index_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:index_scope_type:host-index-values'
    error stop
  end if
  checks = checks + 1
  if (host_index_seen /= 555) then
    write(*,'(a)') 'SCOPE:index_scope_type:host-index-not-declared'
    error stop
  end if
  checks = checks + 1
  if (checks /= 9) then
    write(*,'(a)') 'SCOPE:index_scope_type:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 INDEX SCOPE TYPE OK'
contains
end program scoping_19_3_19_5_index_scope_type
