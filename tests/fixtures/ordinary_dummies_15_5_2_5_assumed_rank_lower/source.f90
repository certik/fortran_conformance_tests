! rule: S15.5.2.5-019
! covers: assumed-rank-lower-bound-one
! evidence: effect
! standard: f2023
module ordinary_dummy_lower_m
  implicit none
contains
  subroutine observe_lower(x, lower_seen)
    integer, intent(in) :: x(..)
    integer, intent(out) :: lower_seen(2)
    select rank (x)
    rank (2)
      lower_seen = lbound(x)
    rank default
      error stop 91
    end select
  end subroutine
end module
program ordinary_dummy_lower
  use ordinary_dummy_lower_m
  implicit none
  integer :: checks = 0, i, j
  integer :: actual(-2:-1,4:6)
  integer :: lower_seen(2) = [-7, -8]
  do j = 4, 6
    do i = -2, -1
      actual(i,j) = 10*j + i
    end do
  end do
  call observe_lower(actual, lower_seen)
  call expect_vector2(lower_seen, [1,1], 'assumed-rank lower bound one')
  call expect_equal(checks, 1, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY LOWER OK'
contains
  subroutine expect_equal(got, want, label)
    integer, intent(in) :: got, want
    character(len=*), intent(in) :: label
    if (got /= want) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'OD15525-FAIL', label, got, want
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_vector2(got, want, label)
    integer, intent(in) :: got(2), want(2)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
    checks = checks + 1
  end subroutine
end program
