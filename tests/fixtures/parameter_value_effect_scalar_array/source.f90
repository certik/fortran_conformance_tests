program parameter_value_scalar_array_effect
  implicit none
  integer :: values(2,2)
  parameter (values=5)
  integer :: visits, returns, observed_checks, main_checks
  visits=0
  returns=0
  observed_checks=0
  main_checks=0
  call observe
  returns=returns+1
  if (visits /= 1) then
    write(*,'(a)') 'PVE:scalar_array:observer-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'PVE:scalar_array:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observed_checks /= 4) then
    write(*,'(a)') 'PVE:scalar_array:observed-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 3) then
    write(*,'(a)') 'PVE:scalar_array:main-check-total'
    error stop
  end if
  write(*,'(a)') 'PARAMETER VALUES SCALAR ARRAY OK'
contains
  subroutine observe
    implicit none
    visits=visits+1
    if (values(1,1) /= 5) then
      write(*,'(a)') 'PVE:scalar_array:element-1-1'
      error stop
    end if
    observed_checks=observed_checks+1
    if (values(2,1) /= 5) then
      write(*,'(a)') 'PVE:scalar_array:element-2-1'
      error stop
    end if
    observed_checks=observed_checks+1
    if (values(1,2) /= 5) then
      write(*,'(a)') 'PVE:scalar_array:element-1-2'
      error stop
    end if
    observed_checks=observed_checks+1
    if (values(2,2) /= 5) then
      write(*,'(a)') 'PVE:scalar_array:element-2-2'
      error stop
    end if
    observed_checks=observed_checks+1
  end subroutine observe
end program parameter_value_scalar_array_effect
