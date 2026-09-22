! rule: S10.2.3.2-012
! covers: where-stmt-selected-elements-assigned
! Sentinels are distinct from every value any WHERE branch can assign.
! Expected values below are hand-written scalar literals; no masking intrinsic is used.
program wm02
  implicit none
  integer :: checks
  integer :: actual(-2:3), rhs(-2:3)
  logical :: mask(-2:3)
  checks=0
  actual(-2)=-902
  actual(-1)=-901
  actual(0)=-900
  actual(1)=-899
  actual(2)=-898
  actual(3)=-897
  rhs(-2)=501
  rhs(-1)=502
  rhs(0)=503
  rhs(1)=504
  rhs(2)=505
  rhs(3)=506
  mask(-2)=.true.
  mask(-1)=.false.
  mask(0)=.true.
  mask(1)=.false.
  mask(2)=.true.
  mask(3)=.false.
  ! Mask true at -2, 0 and 2; false elements must retain sentinels.
  where (mask) actual = rhs

  ! Expected final actual(-2:3) = [501,-901,503,-899,505,-897].
  ! Ignoring the mask would write 502,504,506 into the false positions.
  if (actual(-2) /= 501) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final--2'
    error stop
  end if
  checks=checks+1
  if (actual(-1) /= -901) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final--1'
    error stop
  end if
  checks=checks+1
  if (actual(0) /= 503) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final-0'
    error stop
  end if
  checks=checks+1
  if (actual(1) /= -899) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final-1'
    error stop
  end if
  checks=checks+1
  if (actual(2) /= 505) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final-2'
    error stop
  end if
  checks=checks+1
  if (actual(3) /= -897) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:final-3'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'WM:where_stmt_selected_assigned:check-total'
    error stop
  end if
  write(*,'(a)') 'WHERE MASKING WHERE STMT SELECTED ASSIGNED OK'
end program wm02
