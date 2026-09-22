! rule: S10.2.3.2-001
! covers: top-level-where-construct-initial-then-region
! Sentinels are distinct from every value any WHERE branch can assign.
! Expected values below are hand-written scalar literals; no masking intrinsic is used.
program wm05
  implicit none
  integer :: checks
  integer :: actual(1:6), rhs(1:6)
  logical :: mask(1:6)
  checks=0
  actual(1)=-701
  actual(2)=-702
  actual(3)=-703
  actual(4)=-704
  actual(5)=-705
  actual(6)=-706
  rhs(1)=101
  rhs(2)=102
  rhs(3)=103
  rhs(4)=104
  rhs(5)=105
  rhs(6)=106
  mask(1)=.true.
  mask(2)=.false.
  mask(3)=.true.
  mask(4)=.false.
  mask(5)=.false.
  mask(6)=.true.
  ! Construct control mask true at 1, 3 and 6.
  where (mask)
    actual = rhs
  end where

  ! Expected final actual(1:6) = [101,-702,103,-704,-705,106].
  ! Treating the construct as unmasked would overwrite positions 2,4,5.
  if (actual(1) /= 101) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-1'
    error stop
  end if
  checks=checks+1
  if (actual(2) /= -702) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-2'
    error stop
  end if
  checks=checks+1
  if (actual(3) /= 103) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-3'
    error stop
  end if
  checks=checks+1
  if (actual(4) /= -704) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-4'
    error stop
  end if
  checks=checks+1
  if (actual(5) /= -705) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-5'
    error stop
  end if
  checks=checks+1
  if (actual(6) /= 106) then
    write(*,'(a)') 'WM:construct_initial_then_region:final-6'
    error stop
  end if
  checks=checks+1
  if (checks /= 6) then
    write(*,'(a)') 'WM:construct_initial_then_region:check-total'
    error stop
  end if
  write(*,'(a)') 'WHERE MASKING CONSTRUCT INITIAL THEN REGION OK'
end program wm05
