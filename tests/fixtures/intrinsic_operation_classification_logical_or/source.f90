! rule: S10.1.5.1-005
! covers: logical-or
! Runtime consequence only: 10.1.5.1 classifies operations, but programs observe values/types.
program ioc_logical_or
  implicit none
  integer :: checks
  logical :: t, f, result_tt, result_tf, result_ft, result_ff
  checks=0
  t = .true.
  f = .false.
  ! Complete .OR. truth table: only false and false gives false.
  result_tt = t .or. t
  result_tf = t .or. f
  result_ft = f .or. t
  result_ff = f .or. f
  if (result_tt) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_or:or-true-true'
    error stop
  end if
  if (result_tf) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_or:or-true-false'
    error stop
  end if
  if (result_ft) then
  checks=checks+1
  else
    write(*,'(a)') 'IOC:logical_or:or-false-true'
    error stop
  end if
  if (result_ff) then
    write(*,'(a)') 'IOC:logical_or:or-false-false'
    error stop
  else
  checks=checks+1
  end if
  if (checks /= 4) then
    write(*,'(a)') 'IOC:logical_or:check-total'
    error stop
  end if
  write(*,'(a)') 'INTRINSIC CLASSIFICATION LOGICAL OR OK'
end program ioc_logical_or
