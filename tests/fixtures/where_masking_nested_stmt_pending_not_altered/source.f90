! rule: S10.2.3.2-008
! covers: nested-where-stmt-does-not-change-outer-pending
! Sentinels are distinct from every value any WHERE branch can assign.
! Expected values below are hand-written scalar literals; no masking intrinsic is used.
program wm21
  implicit none
  integer :: checks
  integer :: actual(1:6), then_values(1:6), outer_else_values(1:6)
  logical :: outer_mask(1:6), inner_mask(1:6)
  checks=0
  actual(1)=-801
  actual(2)=-802
  actual(3)=-803
  actual(4)=-804
  actual(5)=-805
  actual(6)=-806
  then_values(1)=101
  then_values(2)=102
  then_values(3)=103
  then_values(4)=104
  then_values(5)=105
  then_values(6)=106
  outer_else_values(1)=301
  outer_else_values(2)=302
  outer_else_values(3)=303
  outer_else_values(4)=304
  outer_else_values(5)=305
  outer_else_values(6)=306
  outer_mask(1)=.true.
  outer_mask(2)=.true.
  outer_mask(3)=.false.
  outer_mask(4)=.false.
  outer_mask(5)=.true.
  outer_mask(6)=.true.
  inner_mask(1)=.true.
  inner_mask(2)=.false.
  inner_mask(3)=.true.
  inner_mask(4)=.false.
  inner_mask(5)=.false.
  inner_mask(6)=.true.
  ! outer=[T,T,F,F,T,T], inner=[T,F,T,F,F,T].
  where (outer_mask)
    where (inner_mask) actual = then_values
  elsewhere
    actual = outer_else_values
  end where

  ! Expected final actual(1:6) = [101,-802,303,304,-805,106].
  ! If the nested statement altered pending like a construct, positions 2 and 5 would be assigned by the outer ELSEWHERE.
  ! The original outer-false positions 3 and 4 prove the outer pending mask was preserved.
  if (actual(1) /= 101) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-1'
    error stop
  end if
  checks=checks+1
  if (actual(2) /= -802) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-2'
    error stop
  end if
  checks=checks+1
  if (actual(3) /= 303) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-3'
    error stop
  end if
  checks=checks+1
  if (actual(4) /= 304) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-4'
    error stop
  end if
  checks=checks+1
  if (actual(5) /= -805) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-5'
    error stop
  end if
  checks=checks+1
  if (actual(6) /= 106) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:final-6'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'WM:nested_stmt_pending_not_altered:check-total'
    error stop
  end if
  write(*,'(a)') 'WHERE MASKING NESTED STMT PENDING NOT ALTERED OK'
end program wm21
