! rule: S10.1.5.1-005
! covers: logical-eqv
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_logical_eqv
  implicit none
  integer :: checks
  logical :: t, f, result_tt, result_tf, result_ft, result_ff
  checks=0
  t = .true.
  f = .false.
  ! Complete .EQV. truth table: equal operands give true, unequal operands false.
  result_tt = t .eqv. t
  result_tf = t .eqv. f
  result_ft = f .eqv. t
  result_ff = f .eqv. f
  if (result_tt) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_eqv:eqv-true-true'
    error stop
  end if
  if (result_tf) then
    write(*,'(a)') 'IOC:logical_eqv:eqv-true-false'
    error stop
  else
  checks=checks+1
  end if
  if (result_ft) then
    write(*,'(a)') 'IOC:logical_eqv:eqv-false-true'
    error stop
  else
  checks=checks+1
  end if
  if (result_ff) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_eqv:eqv-false-false'
    error stop
  end if
  if (checks /= 4) then
    write(*,'(a)') 'IOC:logical_eqv:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION LOGICAL EQV OK'
end program ioc_logical_eqv
