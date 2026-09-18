program parameter_value_integer_effect
  implicit none
  integer :: first, second, remainder
  parameter (first=3, second=7, remainder=mod(28,3))
  integer :: visits, returns, observed_checks, main_checks
  visits=0
  returns=0
  observed_checks=0
  main_checks=0
  call observe
  returns=returns+1
  if (visits /= 1) then
    write(*,'(a)') 'PVE:integer:observer-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'PVE:integer:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observed_checks /= 3) then
    write(*,'(a)') 'PVE:integer:observed-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 3) then
    write(*,'(a)') 'PVE:integer:main-check-total'
    error stop
  end if
  write(*,'(a)') 'PARAMETER VALUES INTEGER OK'
contains
  subroutine observe
    implicit none
    visits=visits+1
    if (first /= 3) then
      write(*,'(a)') 'PVE:integer:first'
      error stop
    end if
    observed_checks=observed_checks+1
    if (second /= 7) then
      write(*,'(a)') 'PVE:integer:second'
      error stop
    end if
    observed_checks=observed_checks+1
    if (remainder /= 1) then
      write(*,'(a)') 'PVE:integer:remainder'
      error stop
    end if
    observed_checks=observed_checks+1
  end subroutine observe
end program parameter_value_integer_effect
