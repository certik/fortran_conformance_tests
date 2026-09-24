! rule: S19.4-006
! covers: implied-do-variable-scope-only-implied-do
! covers: implied-do-variable-scalar
! covers: implicit-rules-control-implied-do-type
! covers: implied-do-variable-not-host-declaration
module scoping_kind_provider
  implicit none
  integer, parameter :: k2 = selected_int_kind(18)
end module

program scoping_19_3_19_5_implied_do_scope_type
  use scoping_kind_provider, only: k2
  implicit integer(kind=k2) (p)
  integer :: checks
  integer :: i, di, host_ac
  integer :: values(3), data_values(3), implicit_kind(1)
  integer :: host_values(3), host_seen
  checks = 0
  i = 99
  di = 88
  host_ac = 444
  values = -1
  implicit_kind = -3
  host_values = -4
  host_seen = -5
  data (data_values(di), di = 1, 3) / 10, 20, 30 /
  values = [(i, i = 1, 3)]
  implicit_kind = [(kind(p), p = 1, 1)]
  block
    host_values = [(host_ac, host_ac = 1, 3)]
    host_seen = host_ac
  end block
  if (any(values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:ac-implied-do-values'
    error stop
  end if
  checks = checks + 1
  if (i /= 99) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:ac-outer-sentinel'
    error stop
  end if
  checks = checks + 1
  if (any(data_values /= [10, 20, 30])) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:data-implied-do-values'
    error stop
  end if
  checks = checks + 1
  if (di /= 88) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:data-outer-sentinel'
    error stop
  end if
  checks = checks + 1
  if (implicit_kind(1) /= k2) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:implicit-kind'
    error stop
  end if
  checks = checks + 1
  if (any(host_values /= [1, 2, 3])) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:host-ac-values'
    error stop
  end if
  checks = checks + 1
  if (host_seen /= 444) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:host-ac-not-declared'
    error stop
  end if
  checks = checks + 1
  if (checks /= 7) then
    write(*,'(a)') 'SCOPE:implied_do_scope_type:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 IMPLIED DO SCOPE TYPE OK'
contains
end program scoping_19_3_19_5_implied_do_scope_type
