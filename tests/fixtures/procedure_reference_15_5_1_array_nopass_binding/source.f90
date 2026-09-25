module procedure_reference_c1529_m
  implicit none
  type t
  contains
    procedure, nopass :: touch
  end type
contains
  subroutine touch()
  end subroutine
end module procedure_reference_c1529_m
program procedure_reference_c1529_invalid
  use procedure_reference_c1529_m
  implicit none
  type(t) :: a(2)
  call a%touch()
end program procedure_reference_c1529_invalid
