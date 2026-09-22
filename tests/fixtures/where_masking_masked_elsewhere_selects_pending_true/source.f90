! rule: S10.2.3.2-004
! covers: masked-elsewhere-selects-prior-pending-and-mask-true
! Sentinels are distinct from every value any WHERE branch can assign.
! Expected values below are hand-written scalar literals; no masking intrinsic is used.
program wm09
  implicit none
  integer :: checks
  integer :: actual(1:6), then_values(1:6), masked_values(1:6), else_values(1:6)
  logical :: first_mask(1:6), second_mask(1:6)
  checks=0
  actual(1)=-711
  actual(2)=-712
  actual(3)=-713
  actual(4)=-714
  actual(5)=-715
  actual(6)=-716
  then_values(1)=101
  then_values(2)=102
  then_values(3)=103
  then_values(4)=104
  then_values(5)=105
  then_values(6)=106
  masked_values(1)=201
  masked_values(2)=202
  masked_values(3)=203
  masked_values(4)=204
  masked_values(5)=205
  masked_values(6)=206
  else_values(1)=301
  else_values(2)=302
  else_values(3)=303
  else_values(4)=304
  else_values(5)=305
  else_values(6)=306
  first_mask(1)=.true.
  first_mask(2)=.false.
  first_mask(3)=.false.
  first_mask(4)=.true.
  first_mask(5)=.false.
  first_mask(6)=.true.
  second_mask(1)=.true.
  second_mask(2)=.true.
  second_mask(3)=.false.
  second_mask(4)=.true.
  second_mask(5)=.false.
  second_mask(6)=.false.
  ! first_mask=[T,F,F,T,F,T], second_mask=[T,T,F,T,F,F].
  where (first_mask)
    actual = then_values
  elsewhere (second_mask)
    actual = masked_values
  elsewhere
    actual = else_values
  end where

  ! Expected final actual(1:6) = [101,202,303,104,305,106].
  ! A masked ELSEWHERE using only second_mask would overwrite positions 1 and 4 with 201 and 204.
  ! A final ELSEWHERE reopening prior branches would overwrite positions already set to 101,202,104,106.
  if (actual(1) /= 101) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-1'
    error stop
  end if
  checks=checks+1
  if (actual(2) /= 202) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-2'
    error stop
  end if
  checks=checks+1
  if (actual(3) /= 303) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-3'
    error stop
  end if
  checks=checks+1
  if (actual(4) /= 104) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-4'
    error stop
  end if
  checks=checks+1
  if (actual(5) /= 305) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-5'
    error stop
  end if
  checks=checks+1
  if (actual(6) /= 106) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:final-6'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'WM:masked_elsewhere_selects_pending_true:check-total'
    error stop
  end if
  write(*,'(a)') 'WHERE MASKING MASKED ELSEWHERE SELECTS PENDING TRUE OK'
end program wm09
