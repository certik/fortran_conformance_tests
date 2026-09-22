! rule: S9.7.1.2-011
! covers: mold-variable-value-need-not-be-defined
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_mold_undefined_value
  implicit none
  integer :: checks
  integer, allocatable :: mold(:,:), a(:,:)
  integer :: stat
  checks=0
  allocate(mold(-6:-4,2:5))
  allocate(a, mold=mold, stat=stat)
  if (stat /= 0) then
    write(*,'(a)') 'AEX:mold_undefined_value:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:mold_undefined_value:allocated'
    error stop
  end if
  checks=checks+1
  if (any(lbound(a) /= [-6,2])) then
    write(*,'(a)') 'AEX:mold_undefined_value:lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(a) /= [-4,5])) then
    write(*,'(a)') 'AEX:mold_undefined_value:upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(a) /= [3,4])) then
    write(*,'(a)') 'AEX:mold_undefined_value:shape'
    error stop
  end if
  checks=checks+1
  a(-6,2)=612
  a(-4,5)=445
  if (a(-6,2) /= 612) then
    write(*,'(a)') 'AEX:mold_undefined_value:written-lower-corner'
    error stop
  end if
  checks=checks+1
  if (a(-4,5) /= 445) then
    write(*,'(a)') 'AEX:mold_undefined_value:written-upper-corner'
    error stop
  end if
  checks=checks+1
  if (checks /= 7) then
    write(*,'(a)') 'AEX:mold_undefined_value:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION MOLD UNDEFINED VALUE OK'
end program allocate_execution_mold_undefined_value
