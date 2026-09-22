! rule: S9.7.1.2-008
! covers: shape-from-source-expr,lower-bounds-from-source-lbound,source-bound-changes-do-not-affect
! Expected bounds, shapes and values are hand-derived from Fortran 2023 9.7.1.2.
program allocate_execution_source_shape_bounds
  implicit none
  integer :: checks
  integer, allocatable :: s(:,:), a(:,:)
  integer :: stat
  checks=0
  allocate(s(-3:-1,5:8))
  s(-3,5)=305
  s(-2,5)=205
  s(-1,5)=105
  s(-3,6)=306
  s(-2,6)=206
  s(-1,6)=106
  s(-3,7)=307
  s(-2,7)=207
  s(-1,7)=107
  s(-3,8)=308
  s(-2,8)=208
  s(-1,8)=108
  allocate(a, source=s, stat=stat)
  deallocate(s)
  allocate(s(11:12,-7:-5))
  s = 719
  if (stat /= 0) then
    write(*,'(a)') 'AEX:source_shape_bounds:stat-success'
    error stop
  end if
  checks=checks+1
  if (.not. (allocated(a))) then
    write(*,'(a)') 'AEX:source_shape_bounds:allocated'
    error stop
  end if
  checks=checks+1
  if (any(lbound(a) /= [-3,5])) then
    write(*,'(a)') 'AEX:source_shape_bounds:lower'
    error stop
  end if
  checks=checks+1
  if (any(ubound(a) /= [-1,8])) then
    write(*,'(a)') 'AEX:source_shape_bounds:upper'
    error stop
  end if
  checks=checks+1
  if (any(shape(a) /= [3,4])) then
    write(*,'(a)') 'AEX:source_shape_bounds:shape'
    error stop
  end if
  checks=checks+1
  if (a(-3,5) /= 305) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-lower-corner'
    error stop
  end if
  checks=checks+1
  if (a(-2,5) /= 205) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-left-middle'
    error stop
  end if
  checks=checks+1
  if (a(-1,5) /= 105) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-left-upper'
    error stop
  end if
  checks=checks+1
  if (a(-3,6) /= 306) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-second-lower'
    error stop
  end if
  checks=checks+1
  if (a(-2,6) /= 206) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-second-middle'
    error stop
  end if
  checks=checks+1
  if (a(-1,6) /= 106) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-second-upper'
    error stop
  end if
  checks=checks+1
  if (a(-3,7) /= 307) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-third-lower'
    error stop
  end if
  checks=checks+1
  if (a(-2,7) /= 207) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-interior'
    error stop
  end if
  checks=checks+1
  if (a(-1,7) /= 107) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-third-upper'
    error stop
  end if
  checks=checks+1
  if (a(-2,8) /= 208) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-right-middle'
    error stop
  end if
  checks=checks+1
  if (a(-1,8) /= 108) then
    write(*,'(a)') 'AEX:source_shape_bounds:value-upper-corner'
    error stop
  end if
  checks=checks+1
  if (any(lbound(s) /= [11,-7])) then
    write(*,'(a)') 'AEX:source_shape_bounds:source-new-lower-control'
    error stop
  end if
  checks=checks+1
  if (a(-3,8) /= 308) then
    write(*,'(a)') 'AEX:source_shape_bounds:a-retained-after-source-change'
    error stop
  end if
  checks=checks+1
  if (checks /= 18) then
    write(*,'(a)') 'AEX:source_shape_bounds:check-total'
    error stop
  end if
  write(*,'(a)') 'ALLOCATE EXECUTION SOURCE SHAPE BOUNDS OK'
end program allocate_execution_source_shape_bounds
