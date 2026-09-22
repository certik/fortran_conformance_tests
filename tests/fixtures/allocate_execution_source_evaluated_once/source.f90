! rule: S9.7.1.2-010
! covers: source-expression-evaluated-once
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_source_evaluated_once
  implicit none
  integer :: checks
  integer, save :: counter
  integer, allocatable :: a
  integer :: stat
  counter=0
  checks=0
  allocate(a, source=produce(), stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:source_evaluated_once:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:source_evaluated_once:allocated'
    error stop
  end if
  checks=checks+1
  if (counter /= 1) then
    write(*,'(a)') 'AEX:source_evaluated_once:counter-once'
    error stop
  end if
  checks=checks+1
  if (a /= 79) then
    write(*,'(a)') 'AEX:source_evaluated_once:source-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'AEX:source_evaluated_once:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION SOURCE EVALUATED ONCE OK'
contains
  integer function produce()
    counter=counter+1
    produce=79
  end function produce
end program allocate_execution_source_evaluated_once
