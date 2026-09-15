! C726 (R721 R722 R723) A type-param-value of * shall be used only
!   - to declare a dummy argument, - to declare a named constant,
!   - in the type-spec of an ALLOCATE statement wherein each allocate-object is a
!     dummy argument of type CHARACTER with an assumed character length,
!   - in the type-spec or derived-type-spec of a type guard statement, or
!   - in an external function, to declare the character length parameter of the
!     function result.
! Each case is its own program unit so that cases cannot interfere.
module c726_component
    implicit none
    type :: t
        character(3) :: s   ! {error C726 component}
    end type
end module
































