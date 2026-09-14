! rule: C601
! covers: length-64
! reference-warnings: long-names
! Each offending name is exactly 64 characters and occurs only once.
! case: variable
subroutine c601_variable
    implicit none
    integer :: name_123456789_123456789_123456789_123456789_123456789_123456789 ! {error C601 variable}
end subroutine
! case: dummy
! Implicit typing avoids repeating the overlong dummy name in a declaration.
subroutine c601_dummy(argu_123456789_123456789_123456789_123456789_123456789_123456789) ! {error C601 dummy}
end subroutine
! case: procedure
integer function proc_123456789_123456789_123456789_123456789_123456789_123456789() result(x) ! {error C601 procedure}
    implicit none
    x = 1
end function
! case: type
module c601_type
    implicit none
    type :: type_123456789_123456789_123456789_123456789_123456789_123456789 ! {error C601 type}
        integer :: x
    end type
end module
! case: component
module c601_component
    implicit none
    type :: t
        integer :: part_123456789_123456789_123456789_123456789_123456789_123456789 ! {error C601 component}
    end type
end module
! case: module
module modu_123456789_123456789_123456789_123456789_123456789_123456789 ! {error C601 module}
    implicit none
end module
! case: program
program prog_123456789_123456789_123456789_123456789_123456789_123456789 ! {error C601 program}
    implicit none
end program
