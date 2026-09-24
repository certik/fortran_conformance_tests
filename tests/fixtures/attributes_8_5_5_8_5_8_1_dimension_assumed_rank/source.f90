program attributes_dimension_assumed_rank
  implicit none
  integer :: scalar
  integer :: rank_one(-1:1)
  integer :: rank_two(2,3)
  integer :: zero_extent(1:0,4)
  integer :: checks
  scalar = 7
  rank_one = [11, 13, 17]
  rank_two = reshape([1, 2, 3, 4, 5, 6], shape(rank_two))
  checks = 0
  call check_scalar(scalar)
  call check_rank_one(rank_one)
  call check_rank_two(rank_two)
  call check_zero_extent(zero_extent)
  call expect_equal(checks, 12, 'check total before completion')
  write(*,'(a)') 'ATTRIBUTES DIMENSION ASSUMED RANK OK'
contains
  subroutine check_scalar(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 0, 'scalar effective rank')
    call expect_equal(size(shape(x)), 0, 'scalar shape vector size')
    call expect_equal(size(x), 1, 'scalar size empty product')
  end subroutine
  subroutine check_rank_one(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 1, 'rank-one effective rank')
    call expect_shape(shape(x), [3], 'rank-one shape')
    call expect_equal(size(x), 3, 'rank-one size')
  end subroutine
  subroutine check_rank_two(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 2, 'rank-two effective rank')
    call expect_shape(shape(x), [2, 3], 'rank-two shape')
    call expect_equal(size(x), 6, 'rank-two size')
  end subroutine
  subroutine check_zero_extent(x)
    integer, intent(in) :: x(..)
    call expect_equal(rank(x), 2, 'zero-extent effective rank')
    call expect_shape(shape(x), [0, 4], 'zero shape')
    call expect_equal(size(x), 0, 'zero total size')
  end subroutine

  subroutine expect_shape(observed, expected, label)
    integer, intent(in) :: observed(:), expected(:)
    character(len=*), intent(in) :: label
    if (size(observed) /= size(expected) .or. any(observed /= expected)) then
      write(*,'(a,1x,a)') 'ATTR-DIM-AR-FAIL', label
      error stop
    end if
    checks = checks + 1
  end subroutine
  subroutine expect_equal(observed, expected, label)
    integer, intent(in) :: observed, expected
    character(len=*), intent(in) :: label
    if (observed /= expected) then
      write(*,'(a,1x,a,1x,i0,1x,i0)') 'ATTR-DIM-AR-FAIL', label, observed, expected
      error stop
    end if
    checks = checks + 1
  end subroutine
end program attributes_dimension_assumed_rank
