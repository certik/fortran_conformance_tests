program i169o_is_contiguous_types
  implicit none
  type :: sample_type
    integer :: n
  end type sample_type
  integer :: ints(6) = [11, 12, 13, 14, 15, 16]
  real :: reals(2) = [1.0, 2.0]
  complex :: complexes(2) = [(1.0, 2.0), (3.0, 4.0)]
  logical :: logicals(2) = [.true., .false.]
  character(len=3) :: chars(2) = ['abc', 'def']
  type(sample_type) :: deriveds(2) = [sample_type(1), sample_type(2)]
  call require_true('is_contiguous accepts whole arrays of every intrinsic and derived type', &
      is_contiguous(ints) .and. is_contiguous(reals) .and. is_contiguous(complexes) .and. &
      is_contiguous(logicals) .and. is_contiguous(chars) .and. is_contiguous(deriveds))
  write(*,'(a)') 'INTRINSICS 16.9.O IS CONTIGUOUS TYPES OK'
contains
  subroutine require_true(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (.not. value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_true
  subroutine require_false(label, value)
    character(len=*), intent(in) :: label
    logical, intent(in) :: value
    if (value) then
      write(*,'(a)') label
      error stop
    end if
  end subroutine require_false
end program i169o_is_contiguous_types
