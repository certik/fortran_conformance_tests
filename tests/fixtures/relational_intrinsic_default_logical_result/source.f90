! rule: S10.1.5.5.1-001
! covers: two-operand-comparison
! Oracle truth values are hand-derived from Fortran 2023 10.1.5.5.1.
program rel_intrinsic_default_logical_result
  implicit none
  integer :: checks
  integer :: left, right
  logical :: observed, false_control
  checks=0
  left = -3
  right = 2
  ! -3 is less than 2, so left < right is true; the reversed comparison is false.
  observed = left < right
  if (.not. (observed)) then
    write(*,'(a)') 'RIF:default_logical_result:two-operand-relation-true'
    error stop
  end if
  checks=checks+1
  false_control = right < left
  if (false_control) then
    write(*,'(a)') 'RIF:default_logical_result:reversed-relation-false'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'RIF:default_logical_result:check-total'
    error stop
  end select
  write(*,'(a)') 'RELATIONAL INTRINSIC DEFAULT LOGICAL RESULT OK'
end program rel_intrinsic_default_logical_result
