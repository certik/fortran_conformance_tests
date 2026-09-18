program parameter_value_logical_effect
  implicit none
  logical :: yes, no
  parameter (yes=.true., no=.false.)
  integer :: visits, returns, observed_checks, main_checks
  visits=0
  returns=0
  observed_checks=0
  main_checks=0
  call observe
  returns=returns+1
  if (visits /= 1) then
    write(*,'(a)') 'PVE:logical:observer-visits'
    error stop
  end if
  main_checks=main_checks+1
  if (returns /= 1) then
    write(*,'(a)') 'PVE:logical:normal-returns'
    error stop
  end if
  main_checks=main_checks+1
  if (observed_checks /= 2) then
    write(*,'(a)') 'PVE:logical:observed-checks'
    error stop
  end if
  main_checks=main_checks+1
  if (main_checks /= 3) then
    write(*,'(a)') 'PVE:logical:main-check-total'
    error stop
  end if
  write(*,'(a)') 'PARAMETER VALUES LOGICAL OK'
contains
  subroutine observe
    implicit none
    visits=visits+1
    if (yes .neqv. .true.) then
      write(*,'(a)') 'PVE:logical:true'
      error stop
    end if
    observed_checks=observed_checks+1
    if (no .neqv. .false.) then
      write(*,'(a)') 'PVE:logical:false'
      error stop
    end if
    observed_checks=observed_checks+1
  end subroutine observe
end program parameter_value_logical_effect
