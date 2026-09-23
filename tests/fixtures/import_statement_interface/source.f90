module import_statement_interface_support
  implicit none
  integer, parameter :: rk = selected_int_kind(9)
  integer, parameter :: slot_count = 2
  integer, parameter :: slot_count_alt = 1
  type :: box
    integer(rk) :: value
  end type
contains
  subroutine run_interface(observed)
    integer(rk), intent(out) :: observed
    interface
      subroutine monitor(item, answer)
        import :: box, rk, slot_count
        type(box), intent(in) :: item(slot_count)
        integer(rk), intent(out) :: answer
      end subroutine
    end interface
    type(box) :: payload(slot_count)
    payload(1)%value = 31_rk
    payload(2)%value = 11_rk
    observed = -77_rk
    call monitor(payload, observed)
  end subroutine
end module import_statement_interface_support

subroutine monitor(item, answer)
  use import_statement_interface_support, only: box, rk, slot_count
  implicit none
  type(box), intent(in) :: item(slot_count)
  integer(rk), intent(out) :: answer
  integer :: i
  answer = 0_rk
  do i = 1, size(item)
    answer = answer + item(i)%value
  end do
end subroutine monitor

program import_statement_interface_effect
  use import_statement_interface_support, only: rk, run_interface
  implicit none
  integer(rk) :: observed
  observed = -99_rk
  call run_interface(observed)
  if (observed /= 42_rk) error stop 1
  write(*,'(a)') 'IMPORT STATEMENT INTERFACE OK'
end program import_statement_interface_effect
