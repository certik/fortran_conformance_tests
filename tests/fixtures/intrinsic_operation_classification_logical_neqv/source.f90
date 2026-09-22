! rule: S10.1.5.1-005
! covers: logical-neqv
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_logical_neqv
  implicit none
  integer :: checks
  logical :: t, f, result_tt, result_tf, result_ft, result_ff
  checks=0
  t = .true.
  f = .false.
  ! Complete .NEQV. truth table: unequal operands give true, equal operands false.
  result_tt = t .neqv. t
  result_tf = t .neqv. f
  result_ft = f .neqv. t
  result_ff = f .neqv. f
  if (result_tt) then
    write(*,'(a)') 'IOC:logical_neqv:neqv-true-true'
    error stop
  else
  checks=checks+1
  end if
  if (result_tf) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_neqv:neqv-true-false'
    error stop
  end if
  if (result_ft) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_neqv:neqv-false-true'
    error stop
  end if
  if (result_ff) then
    write(*,'(a)') 'IOC:logical_neqv:neqv-false-false'
    error stop
  else
  checks=checks+1
  end if
  if (checks /= 4) then
    write(*,'(a)') 'IOC:logical_neqv:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION LOGICAL NEQV OK'
end program ioc_logical_neqv
