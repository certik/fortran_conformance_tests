program bind_common_retention
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  interface
    subroutine store_pair(left_value, right_value, visits)
      use, intrinsic :: iso_c_binding, only: c_int
      implicit none
      integer(c_int), intent(in) :: left_value, right_value
      integer(c_int), intent(inout) :: visits
    end subroutine store_pair
    subroutine load_pair(left_value, right_value, visits)
      use, intrinsic :: iso_c_binding, only: c_int
      implicit none
      integer(c_int), intent(out) :: left_value, right_value
      integer(c_int), intent(inout) :: visits
    end subroutine load_pair
  end interface
  integer(c_int) :: left_input, right_input, left_observed, right_observed
  integer(c_int) :: writer_visits, reader_visits, checks, cycles
  writer_visits=0_c_int
  reader_visits=0_c_int
  checks=0_c_int
  cycles=0_c_int
  left_input=11_c_int
  right_input=13_c_int
  call store_pair(left_input, right_input, writer_visits)
  if (writer_visits /= 1_c_int) error stop 'BCS:writer-first'
  checks=checks+1_c_int
  call load_pair(left_observed, right_observed, reader_visits)
  if (reader_visits /= 1_c_int) error stop 'BCS:reader-first'
  checks=checks+1_c_int
  if (left_observed /= 11_c_int) error stop 'BCS:left-first'
  checks=checks+1_c_int
  if (right_observed /= 13_c_int) error stop 'BCS:right-first'
  checks=checks+1_c_int
  cycles=cycles+1_c_int
  if (cycles /= 1_c_int) error stop 'BCS:cycle-first'
  checks=checks+1_c_int
  left_input=17_c_int
  right_input=19_c_int
  call store_pair(left_input, right_input, writer_visits)
  if (writer_visits /= 2_c_int) error stop 'BCS:writer-second'
  checks=checks+1_c_int
  call load_pair(left_observed, right_observed, reader_visits)
  if (reader_visits /= 2_c_int) error stop 'BCS:reader-second'
  checks=checks+1_c_int
  if (left_observed /= 17_c_int) error stop 'BCS:left-second'
  checks=checks+1_c_int
  if (right_observed /= 19_c_int) error stop 'BCS:right-second'
  checks=checks+1_c_int
  cycles=cycles+1_c_int
  if (cycles /= 2_c_int) error stop 'BCS:cycle-second'
  checks=checks+1_c_int
  if (checks /= 10_c_int) error stop 'BCS:check-total'
  write(*,'(a)') 'BIND COMMON SAVE OK'
end program bind_common_retention

subroutine store_pair(left_value, right_value, visits)
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), intent(in) :: left_value, right_value
  integer(c_int), intent(inout) :: visits
  integer(c_int) :: first, second
  common /saved_pair/ first, second
  bind(c) :: /saved_pair/
  first=left_value
  second=right_value
  visits=visits+1_c_int
end subroutine store_pair

subroutine load_pair(left_value, right_value, visits)
  use, intrinsic :: iso_c_binding, only: c_int
  implicit none
  integer(c_int), intent(out) :: left_value, right_value
  integer(c_int), intent(inout) :: visits
  integer(c_int) :: first, second
  common /saved_pair/ first, second
  bind(c) :: /saved_pair/
  left_value=first
  right_value=second
  visits=visits+1_c_int
end subroutine load_pair
