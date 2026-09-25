! rule: S15.5.2.5-019
! covers: assumed-rank-upper-bound-extent
! evidence: effect
! standard: f2023
module ordinary_dummy_rank_m
  implicit none
  type :: sink
    integer :: vals(2) = [-9, -8]
  end type
  interface generic_sum
    module procedure sum_rank_one
  end interface
  interface operator(.twice.)
    module procedure twice_rank_one
  end interface
  interface assignment(=)
    module procedure assign_rank_one
  end interface
contains
  subroutine scalar_only(x, out)
    integer, intent(in) :: x
    integer, intent(out) :: out
    out = x
  end subroutine
  subroutine assumed_rank_observe(x, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
    integer, intent(in) :: x(..)
    integer, intent(out) :: rank_seen, shape_seen(2), lower_seen(2), upper_seen(2), value_seen
    shape_seen = [-7, -8]
    lower_seen = [-9, -10]
    upper_seen = [-11, -12]
    value_seen = -13
    select rank (x)
    rank (0)
      rank_seen = 0
      value_seen = x
    rank (1)
      rank_seen = 1
      shape_seen = [size(x), -8]
      lower_seen = [lbound(x, 1), -10]
      upper_seen = [ubound(x, 1), -12]
      value_seen = x(1)
    rank (2)
      rank_seen = rank(x)
      shape_seen = shape(x)
      lower_seen = lbound(x)
      upper_seen = ubound(x)
      value_seen = x(2,2)
    rank default
      error stop 91
    end select
  end subroutine
  subroutine assumed_shape_observe(x, shape_seen, value_seen)
    integer, intent(in) :: x(:,:)
    integer, intent(out) :: shape_seen(2), value_seen
    shape_seen = shape(x)
    value_seen = x(2,3)
  end subroutine
  integer function sum_rank_one(x)
    integer, intent(in) :: x(:)
    sum_rank_one = sum(x)
  end function
  function twice_rank_one(x) result(out)
    integer, intent(in) :: x(:)
    integer :: out(size(x))
    out = 2*x
  end function
  subroutine assign_rank_one(lhs, rhs)
    type(sink), intent(out) :: lhs
    integer, intent(in) :: rhs(:)
    lhs%vals = rhs
  end subroutine
  subroutine array_order(x, before, after)
    integer, intent(inout) :: x(2,3)
    integer, intent(out) :: before, after
    before = x(2,2)
    x(2,2) = 144
    after = x(2,2)
  end subroutine
end module
program ordinary_dummy_rank
  use ordinary_dummy_rank_m
  implicit none
  integer :: checks = 0, out = -31, rank_seen = -32, value_seen = -33
  integer :: shape_seen(2) = [-1, -2], lower_seen(2) = [-3, -4], upper_seen(2) = [-5, -6]
  integer :: actual_rank2(2,3), shape_actual(2,3), bound_vec(4)
  integer :: order_actual(2,3), before = -34, after = -35
  type(sink) :: assigned
  call scalar_only(41, out)
  call expect_equal(out, 41, 'noncoindexed scalar actual scalar dummy')
  call assumed_rank_observe(53, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_equal(rank_seen, 0, 'assumed-rank scalar exception rank')
  call expect_equal(value_seen, 53, 'assumed-rank accepts scalar value')
  actual_rank2 = reshape([1,2,3,4,5,6], [2,3])
  call assumed_rank_observe(actual_rank2, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_equal(rank_seen, 2, 'assumed-rank array rank')
  call expect_vector2(shape_seen, [2,3], 'assumed-rank array extents')
  call expect_vector2(lower_seen, [1,1], 'assumed-rank array lower controls')
  call expect_equal(value_seen, 4, 'assumed-rank array value')
  bound_vec = [8,9,10,11]
  call assumed_rank_observe(bound_vec, rank_seen, shape_seen, lower_seen, upper_seen, value_seen)
  call expect_vector2(upper_seen, [4,-12], 'assumed-rank upper bound extent')
  shape_actual = reshape([7,8,9,10,11,12], [2,3])
  call assumed_shape_observe(shape_actual, shape_seen, value_seen)
  call expect_vector2(shape_seen, [2,3], 'assumed-shape same rank shape')
  call expect_equal(value_seen, 12, 'assumed-shape value')
  call expect_equal(generic_sum([2,4]), 6, 'generic nonelemental rank agreement')
  call expect_vector2(.twice. [6,8], [12,16], 'defined operator rank agreement')
  assigned = [3,5]
  call expect_vector2(assigned%vals, [3,5], 'defined assignment rank agreement')
  order_actual = reshape([11,22,33,44,55,66], [2,3])
  call array_order(order_actual, before, after)
  call expect_equal(before, 44, 'array element order entry')
  call expect_equal(after, 144, 'array element order dummy update')
  call expect_vector6(reshape(order_actual, [6]), [11,22,33,144,55,66], 'array element order caller update')
  call expect_equal(checks, 16, 'check count')
  write(*,'(a)') 'ORDINARY DUMMY RANK OK'
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
  subroutine expect_vector6(got, want, label)
    integer, intent(in) :: got(6), want(6)
    character(len=*), intent(in) :: label
    if (any(got /= want)) error stop label
    checks = checks + 1
  end subroutine
end program
